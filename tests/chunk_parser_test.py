import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models

ex1 = "<think>reasoning goes here</think>response goes here"
ex2 = "<think>reasoning goes here</thi"


def test_example(example: str):
    res = models.ChatGenerationResult()
    for i in range(len(example)):
        char = example[i]
        chunk = res.add_chunk({"response_delta": char, "reasoning_delta": ""})
        print(i, ":", chunk)

    print("output", res.output())


if __name__ == "__main__":
    # test_example(ex1)
    test_example(ex2)
    