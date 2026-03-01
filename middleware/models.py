from pydantic import BaseModel

class IVRRequest(BaseModel):
    call_id: str
    input: str
    input_type: str  # speech or dtmf