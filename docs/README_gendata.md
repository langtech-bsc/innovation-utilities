# 📚 gendata

**gendata** is a CLI tool for generating datasets using prompt-driven tasks and pluggable model APIs like OpenAI or local deployments. It supports JSON/YAML configuration, parallel execution, and flexible output formatting.

---

## 🔧 Installation

You can install `gendata` using **Poetry** or **pip** with optional extras (no `torch` needed unless you use speech extras).

### ▶️ Using Poetry

```bash
git clone https://github.com/langtech-bsc/innovation-utilities.git
cd innovation
poetry install --with gendata
```

### ▶️ Using pip (no `torch`, with data generation support)

```bash
pip install git+https://github.com/langtech-bsc/innovation-utilities.git#egg=innovation[gendata]
```


---

## 🚀 Quick Start

Use `torchrun` for multi-process execution:

```bash
torchrun --nproc_per_node=5 -m innovation.gendata \
  --input persona.jsonl \
  --output output/data.jsonl \
  --model openai \
  --task task.yml \
  --model-params model_params.yml \
  --model-args="api_url=http://localhost:8080/v1/,model=DeepSeek-V3,api_key=your_api_key" \
  --wait-for-model
```

---

## ⚙️ Command-line Options

| Argument                          | Description                                                                 | Required | Example                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|----------|-------------------------------------------------------------------------|
| `--input INPUT`                   | Path to input dataset                                                       | ✅        | `--input data/input.json`                                              |
| `--output OUTPUT`                 | Path to output dataset                                                      | ✅        | `--output data/output.json`                                            |
| `--data-method {default}`         | Data type/method to generate                                                | ❌        | `--data-method default`                                                |
| `--model {openai}`                | Model API name                                                              | ✅        | `--model openai`                                                       |
| `--unique-key UNIQUE_KEY`        | Unique field for tracking output (default: index)                           | ❌        | `--unique-key uuid`                                                    |
| `--task TASK`                     | Task configuration in JSON or YAML format                                   | ✅        | `--task tasks/summarize.yml`                                           |
| `--model-args MODEL_ARGS`         | Inline model args (e.g. API URL, model name)                                | ❌        | `--model-args api_url=...,model=...,api_key=...`                                   |
| `--model-params MODEL_PARAMS`     | YAML file with additional model config                                      | ❌        | `--model-params config/openai.yaml`                                    |
| `--data-args DATA_ARGS`           | Inline arguments for data generation — these depend on the selected data method. No arguments are needed for the `default` method.need.                                        | ❌        | `--data-args seed=42,temperature=0.7`                                  |
| `--list-data-methods`             | List available data generation methods                                      | ❌        | `--list-data-methods`                                                  |
| `--list-model-apis`               | List available model APIs                                                   | ❌        | `--list-model-apis`                                                    |
| `--wait-for-model`                | Retry connection if model is unavailable                                    | ❌        | `--wait-for-model`                                                     |
| `--finish`                        | Finalize and move any temporary results to output                           | ❌        | `--finish`                                                             |
| `--generate-task-sample`          | Generate a sample task file (simple or complex)                             | ❌        | `--generate-task-sample simple`                                        |
| `--generate-model-params`         | Generate a sample model parameters YAML file                                | ❌        | `--generate-model-params openai`                                       |

---

## Structure of the Task YAML file for the `default` data-method

### 📌 Key Concepts


#### ✅ `messages_list`

A list of message blocks (System/User). Each block is **one task** for the model.  

- Only **user** message is required.
- **system** message is optional and usually provides context/instruction.
- Each message outputs **one result**.
- The number of items in `messages_list`, `output_keys`, and `output_types` must match.


#### ✅ Sequential Field Use

Each generated response can be reused later.  

For example:

- If step 1 creates `use_case`,  

- Step 2 can refer to `{use_case}`.  

This continues across all messages.


#### ✅ `output_keys`

Determines the result of each message, which is saved in the output dataset using the matching key.

- Example: `["use_case", "conversations", "system_prompt"]`


#### ✅ `output_types`

Type of each output.  

- Only two allowed: `json` or `str`.

- Example: `["str", "json", "str"]`

#### ✅ `random_extra_keys`

Extra fields randomly injected into each row.  

- Example: `language` (can be "English", "Spanish", "Catalán", any other language)


These fields are available for **all messages** in that row.


---


### ✅ Summary Rules

- Output types must be valid (`json`, `str`).
- Outputs must match expected structure.
- Use `{{ }}` for curly braces in JSON.
- Messages follow the order and use fields generated before.
- You can **reference or use** previously created keys in later messages.
- You **must** generate one valid response per user message.

---

### Example YAML file

```yaml
random_extra_keys:
  language:
    - English
    - Spanish

output_keys:
  - use_case
  - conversation
  - system_prompt

output_types:
  - str
  - json
  - str

messages_list:
  - user: |
      Give me a use case for function calling using this persona in {language}:
      {persona}
  - user: |
      create conversation depending on use case in {language}: {use_case}
  - system: |
      You're an AI assistant creating a system prompt in {language}.
    user: |
      Based on this use case: {use_case}
      And conversation: {conversation}
      Create a system prompt.
```

---

## 📝 Example: Model Params YAML (`model_params.yml`)

```yaml
temperature: 0.3
max_tokens: 10000
```

---

## 🧰 Extras & Templates

You can generate starter files using:

```bash
python -m innovation.gendata --generate-task-sample simple
python -m innovation.gendata --generate-model-params openai
```



## 📌 Tips

- For stable datasets across reruns, specify a unique key with `--unique-key`.
- Use `--wait-for-model` if you're working with remote/local models that may take time to start.
- Run with `torchrun` for distributed processing across multiple workers.
