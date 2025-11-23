import os
import pickle
from urllib.parse import quote
import json
import sqlite3
import os

import requests
from bs4 import BeautifulSoup, Tag

from tree_node import TreeNode
from source import Source
from sqlite_connection import SqliteConnection

db_path = "store.db"

def main():
    sources = get_sources("to_watch.json")
    if not os.path.isfile(db_path):
        initialize_db(db_path)
    conn = SqliteConnection(db_path).connection
    assert conn is not None
    cur = conn.cursor()

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0"

    headers = {"User-Agent": user_agent}

    snapshots = cur.execute("SELECT * FROM snapshots").fetchall()
    urls_saved = [s[0] for s in snapshots]
    for source in sources:
        data = None
        cache_file_name = "cache/" + quote(f"{source.url}.html", safe="")
        fresh_fetch = False
        res = None
        if os.path.isfile(cache_file_name):
            print(f"Reading from cache file {cache_file_name}")
            with open(cache_file_name, "r", encoding="utf-8") as f:
                data = f.read()
        else:
            print(f"requesting {source.url}")
            res = requests.get(source.url, headers=headers)
            data = res.text
            with open(cache_file_name, "w", encoding="utf-8") as f:
                f.write(data)

        if not fresh_fetch or (res and res.status_code == 200):
            soup = BeautifulSoup(data, "html.parser")
            root = create_tree(soup)
            if source.url not in urls_saved:
                print("New source found, storing snapshot")
                save_tree(source.url, root, conn)
            else:
                pass
                #compare_to_older_version(source, root, cur)
        else:
            raise RuntimeError(
                f"Request response was not sucessful: {res.status_code}\nresponse:\n{data}"
            )

    conn.close()

def create_tree(root) -> TreeNode:
    child_nodes: list[TreeNode] = []
    for child in root.children:
        if isinstance(child, Tag):
            child_node = create_tree(child)
            child_nodes.append(child_node)

    return TreeNode(root.tag, root.attrs, child_nodes)


def save_tree(url: str, node: TreeNode, db_conn: sqlite3.Connection):
    cursor = db_conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS snapshots (url TEXT PRIMARY KEY, tree_structure blob)"
    )
    cursor.execute(
        "INSERT INTO snapshots (url, tree_structure) VALUES(?, ?)",
        [url, pickle.dumps(node)],
    )
    db_conn.commit()


def compare_to_older_version(source: Source, node: TreeNode, db_cur: sqlite3.Cursor):
    res = db_cur.execute("SELECT url, tree_structure FROM snapshots WHERE url = ?", (source.url,))
    record = res.fetchone()
    if record:
        older_version = pickle.loads(record[1])
        if has_changed(node, older_version):
            print("has changed")


def has_changed(node: TreeNode, old_node: TreeNode):
    if node.hash != old_node.hash:
        changed = []
        for i, child in enumerate(old_node.children):
            """
            I don't know how to find the child that is actually changed using the hash
            might need to find another way to find the changes
            if i'm going to add a file fro poeple to add as css selector, I might need to use that
            """
            pass

    return False

def get_sources(file_name: str) -> list["Source"]:
    sources_data = None
    with open(file_name, 'r') as f:
        sources_data = json.load(f)

    sources = [Source(url, data["selectors"]) for url, data in sources_data.items()]

    return sources

def initialize_db(db_path: str):
    conn = SqliteConnection(db_path).connection
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS snapshots (url TEXT PRIMARY KEY, tree_structure blob)"
    )
    conn.commit()


if __name__ == "__main__":
    main()
