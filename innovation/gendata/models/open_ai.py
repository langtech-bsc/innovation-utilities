from innovation.gendata.models.model_manager import ModelManager, BaseModel
from openai import OpenAI
from innovation.gendata.utils.logger import setup_logger
import time

logger = setup_logger(__name__)

class TokenLimitError(Exception):
    pass

@ModelManager.register("openai")
class OpenAIChat(BaseModel):
    def __init__(self, api_url="http://localhost:8080/v1/", api_key="xyz", model="tgi", model_params={}):
        self.api_url = api_url
        self.model = model
        self._api_key = api_key
        self._client = OpenAI(base_url=self.api_url, api_key=api_key)

        default_params = { "max_tokens": 5000, "temperature": 0.2}
        self.model_params = self._get_params(model_params, default_params, {"model", "messages", "stream", "api_key", "api_url"})

    def get_model_name(self):
        return self.model

    def get_response(self, messages, wait_for_connection=False):
        params = {"model": self.model, "messages": messages, "stream": False}
        params.update(self.model_params)
        first = True
        while wait_for_connection or first:
            try:
                first = False
                logger.debug("Calling chat.completions.create()")
                response = self._client.chat.completions.create(**params)
                if response.choices[0].finish_reason == 'length':
                    error_msg = (
                        f"Failed to generate response: the `max_tokens` value is too low. "
                        f"Current setting: {self.model_params.get('max_tokens')}. Please increase it."
                    )
                    raise TokenLimitError(error_msg)
                return response.choices[0].message.content
            
            except TokenLimitError as err:
                logger.error(f"OpenAI API: {err}")
                raise
            except Exception as err:
                msg = ". Waiting for connection to be established..." if wait_for_connection else ""
                logger.error(f"Openai API {err}{msg}")
                if not wait_for_connection:
                    raise err
                else:
                    time.sleep(60)

