from helpers import message_queue as mq


class DummyOutput:
    pass


class DummyContext:
    def __init__(self):
        self.data = {}
        self.output = DummyOutput()

    def get_data(self, key):
        return self.data.get(key)

    def set_data(self, key, value):
        self.data[key] = value

    def set_output_data(self, key, value):
        setattr(self.output, key, value)


def test_add_syncs_queue_output_without_context_message_queue_attribute():
    context = DummyContext()

    item = mq.add(context, "hello", ["queued.png"])

    assert item["id"]
    assert mq.get_queue(context)[0]["text"] == "hello"
    assert context.output.message_queue == [
        {
            "id": item["id"],
            "seq": 1,
            "text": "hello",
            "attachments": ["queued.png"],
            "attachment_count": 1,
        }
    ]
