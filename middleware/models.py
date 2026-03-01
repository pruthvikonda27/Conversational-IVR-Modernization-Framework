from pydantic import BaseModel, Field

class CallInput(BaseModel):
    call_id: str = Field(..., example="CALL123")
    input: str = Field(..., example="1")
    input_type: str = Field(..., example="dtmf")