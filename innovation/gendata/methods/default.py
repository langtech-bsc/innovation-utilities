from innovation.gendata.methods.method_manager import MethodManager, BaseMethod, GetLLMResponseType, MessagesType
from typing import Dict, Any, List
import json
from innovation.gendata.utils.logger import setup_logger

logger = setup_logger(__name__)


@MethodManager.register("default")
class Default(BaseMethod):
    def __init__(self, input: str, output: str, global_rank:int, wait_for_model:bool, messages_list: List[MessagesType], unique_key, output_keys, output_types, random_extra_keys):
        super().__init__(input, output, global_rank, wait_for_model, messages_list, unique_key, output_keys, output_types, random_extra_keys)

    def generate_data(self, index, get_llm_response: GetLLMResponseType) -> Dict[str, Any]:
        logger.debug(f"Generating data for field {index}.")
        
        # Extract data for the current index and update it with extra keys
        json_data = self._data.iloc[index].to_dict()
        json_data.update(self.get_extra_keys(index))
        used_keys = []
        
        # Iterate through the messages list to generate responses for each task
        for i, messages in enumerate(self.messages_list):
            # Log the task processing start
            used_keys.extend(self.replaceable_keys[i])
            logger.debug(f"Generating response for task {i} of field {index}.")
            messages = self.generate_messages(json_data, i)
            logger.debug(f"Messages: (task: {i}, field: {index}):\n{json.dumps(messages, indent=4, ensure_ascii=False)}")
            
            response = get_llm_response(messages=messages, wait_for_connection=self.wait_for_model)
            logger.debug(f"LLM Response: (task: {i}, field: {index}):\n{response}")
            
            # If the response type is JSON, convert it to JSON format
            if self.output_types[i] == "json":
                logger.debug(f"Converting response to JSON: (task: {i}, field: {index})")
                try:
                    response = json.loads(response)
                except Exception as e:
                    logger.error(f"Faild to converte response to JSON: (task: {i}, field: {index})\nError: {e}")
                    if json_data.get("json_convertion_error", None) is None:
                        json_data["json_convertion_error"] = []
                    json_data["json_convertion_error"].append(self.output_keys[i])

            json_data[self.output_keys[i]] = response
        
        # Log that all tasks have been completed for the current field (index)
        logger.debug(f"Generating data for field {index} done.")
        used_keys.extend(self.output_keys)
        # Return the filtered json_data with only the relevant keys
        return {key: json_data[key] for key in used_keys if key in json_data}