def vxml_response(message, gather=False):
    if gather:
        return f"""
        <Response>
            <Gather input="dtmf speech" timeout="5">
                <Say>{message}</Say>
            </Gather>
        </Response>
        """
    else:
        return f"""
        <Response>
            <Say>{message}</Say>
        </Response>
        """