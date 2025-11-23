from xxhash import xxh3_64
import pickle

class TreeNode:

    def __init__(self, tag: str, attributes: list[str], children: list["TreeNode"]):
        self.tag = tag
        self.attributes = attributes
        self.children = children
        self.hash = xxh3_64(pickle.dumps(self)).digest()
