route inbound emails to agent chats
input new email sender subject body and existing chats with history
relates to existing chat same topic same sender reply CONTINUE context_id
else reply NEW_CHAT
history determines topic relevance
respond exactly one line ACTION context_id reason

examples
NEW_CHAT _ new request from user
CONTINUE ctx_abc123 same topic about deployment
