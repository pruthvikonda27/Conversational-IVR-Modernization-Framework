def vxml_say(message):
    return f"""
<Response>
    <Say>{message}</Say>
</Response>
"""

def vxml_gather(message):
    return f"""
<Response>
    <Gather input="dtmf speech">
        <Say>{message}</Say>
    </Gather>
</Response>
"""