import argparse
import os
import torch
import torch.distributed as dist
from innovation.gendata.methods.method_manager import MethodManager, BaseMethod
from innovation.gendata.models.model_manager import ModelManager, BaseModel
import importlib
from innovation.gendata.utils.logger import setup_logger
from innovation.gendata.utils import utils
import time

logger = setup_logger(__name__)


def init_distributed():
    
    """Initialize distributed processing with MPI backend."""

    # Check if the environment variables are set by torchrun
    
    if 'MASTER_ADDR' not in os.environ:
        os.environ['MASTER_ADDR'] = 'localhost'  # Set the master node address (use 'localhost' or the actual master node)
        os.environ['MASTER_PORT'] = '29500'

    rank = int(os.environ.get('RANK', 0))  # Default rank 0 if not set
    world_size = int(os.environ.get('WORLD_SIZE', 1))  # Default world size 1 if not set
    
    # If not using torchrun, set the default rank to 0 manually
    if 'RANK' not in os.environ:
        os.environ['RANK'] = str(rank)
        os.environ['WORLD_SIZE'] = str(world_size)
        
    dist.init_process_group(backend="gloo")  # Or "gloo" for CPU-only

    world_size = dist.get_world_size()  # Total number of processes
    global_rank = dist.get_rank()  # Rank of current process
    ngpus = torch.cuda.device_count()
    local_rank = global_rank % ngpus if ngpus != 0 else -1 # Rank within node (GPU ID)

    return world_size, global_rank, local_rank


class SyntheticDataGenerator:

    @classmethod
    def run(cls, method, method_args, model, model_args, input, output, wait_for_model, finish, global_rank, world_size):
        model_instance:BaseModel = ModelManager.get_class(model)(**model_args)
        data_instance:BaseMethod = MethodManager.get_class(method)(input, output, global_rank, wait_for_model, **method_args)

        if global_rank == 0:
            model_instance.print_args()
            data_instance.print_args()
        torch.distributed.barrier()

        start_time = time.time()
        if not finish:
            total = len(data_instance)
            local_size = total // world_size
            remainder = total % world_size

            # Distribute remainder elements across initial ranks
            if global_rank < remainder:
                start_idx = global_rank * (local_size + 1)
                end_idx = start_idx + local_size + 1
            else:
                start_idx = global_rank * local_size + remainder
                end_idx = start_idx + local_size
            
            model = model_instance.get_model_name()
            logger.info(f"Starting generating data.")
            for i in range(start_idx, end_idx):
                start_time_tmp = time.time()
                if not data_instance.is_done(i):
                    data = data_instance.generate_data(i, model_instance.get_response)
                    data[data_instance.unique_key] = data_instance.get_unique_id(i)
                    data["model"] = model
                    data_instance.set_record(data, i)

                    execution_time = time.time() - start_time_tmp
                    logger.info(f"Record {i}/{end_idx} processed in time: {execution_time:.6f} seconds")
                else:
                    logger.info(f"Record {i}/{end_idx} skiped.")

        torch.distributed.barrier()
        if global_rank == 0:
            execution_time = time.time() - start_time
            data_instance.save_all()
            logger.info(f"Saved all record.")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="Path to input dataset.")
    parser.add_argument("--output", type=str, help="Path to output dataset.")
    parser.add_argument("--data-method", default="default", choices=MethodManager.list_classes(), type=str, help="Data type to generate.")
    parser.add_argument("--model", type=str, choices=ModelManager.list_classes(), help="Model to use to generate response.")
    parser.add_argument("--unique-key", type=str, default=None, help="A unique key from the dataset, by default is `id`.")
    parser.add_argument("--task", type=str, help="A json file containing messages_list, list of output_keys and output_types.")
    parser.add_argument("--model-args", type=str, default=None, help=f"Arguments for the method should be separated by commas. Example: 'api_url=http://localhost:8080/v1/,api_key=none,model=tgi'.")
    parser.add_argument("--model-params", type=str, default=None, help="Path to a yaml file containing extra paramters.")
    parser.add_argument("--data-args", type=str, help="Arguments for the method should be separated by commas. Example: --data_args='my_key=my_value,...'.")
    parser.add_argument("--list-data-methods", action="store_true", help="List all available methods to generate dataset.")
    parser.add_argument("--list-model-apis", action="store_true", help="List all available models.")
    parser.add_argument("--wait-for-model", action="store_true", help="Wait for the model, if not available it will keep wait in a loop, this si good if your connection is not stable.")
    parser.add_argument("--finish", action="store_true", help="Complete generating dataset, if any data is saved in temporary files and will be moved to the output path.")
    parser.add_argument("--generate-task-sample", type=str, default=None, choices=["simple", "complex"], help="Generate a example task file.")
    parser.add_argument("--generate-model-params", type=str, default=None, choices=["openai"], help="Generate a example model parameters file.")
    import sys

    world_size, global_rank, _ = init_distributed()


    if '--help' in sys.argv:
        # Only print the help message when rank == 0
        if dist.is_initialized():
            rank = dist.get_rank()
            if rank == 0:
                parser.print_help()
            dist.barrier()  # Ensure all processes reach this point
        else:
            parser.print_help()
        return
    # Initialize distributed processing

    args = parser.parse_args()
    current_dir = os.path.dirname(__file__)

    # Ensure required arguments are provided unless --list-methods is used
    if args.list_data_methods:
        if global_rank == 0:
            print()
            print("\nAvailable data methods:", list(MethodManager.list_classes()))
        return
    if args.list_model_apis:
        if global_rank == 0:
            print("\nAvailable model methods:", list(ModelManager.list_classes()))
        return
    if args.generate_task_sample:
        if global_rank == 0:
            file_path = os.path.join(current_dir, 'tasks_examples', f'{args.generate_task_sample}.yml')
            output_file = "task_example.yml"
            utils.copy_yaml(file_path, output_file)
            print("Created: " + output_file)
        return
    
    if args.generate_model_params:
        if global_rank == 0:
            file_path = os.path.join(current_dir, 'models_examples', f'{args.generate_model_params}.yml')
            output_file = "model_params_example.yml"
            utils.copy_yaml(file_path, output_file)
            print("Created: " + output_file)
        return
    
    errors = []

    # Check for required arguments and append errors to the list
    if not args.input:
        errors.append("--input")
    if not args.output:
        errors.append("--output")
    if not args.task:
        errors.append("--task")
    if not args.data_method:
        errors.append("--data-method")
    if not args.model:
        errors.append("--model")
    
    if not args.unique_key:
        logger.warning("A unique key was not provided (--unique-key). By default, the field index will be used. Ensure that the input dataset remains unchanged each time the task is executed, or provide a unique key for each field to enable accurate detection.")
    if errors:
        if global_rank == 0:
            parser.error(",".join(errors) + " are required.")
        return
    
    if global_rank == 0:
        if os.path.exists(args.output):
            tmp_path_patter, _ = utils.generate_tmp_paths(args.output, 0)
            raise FileExistsError(f"Output path '{args.output}' already exists. Please choose a different path, remove the existing file or move to {tmp_path_patter}, to skip this data (You must replace * by any text of number).")
        parent_dir = os.path.dirname(args.output)
        if parent_dir:  # Only try to create if there's a directory part
            os.makedirs(parent_dir, exist_ok=True)

    torch.distributed.barrier()

    task = utils.read_yaml(args.task)

    data_args = dict(pair.split('=') for pair in args.data_args.split(',')) if args.data_args else {}
    data_args.update(task)
    data_args["unique_key"] = args.unique_key

    model_args = dict(pair.split('=') for pair in args.model_args.split(',')) if args.model_args else {}
    model_args["model_params"] = utils.read_yaml(args.model_params) if args.model_params else {}

    SyntheticDataGenerator.run(args.data_method, data_args, args.model, model_args, args.input, args.output, args.wait_for_model, args.finish, global_rank, world_size)
    torch.distributed.barrier()
if __name__ == "__main__":
    main()



