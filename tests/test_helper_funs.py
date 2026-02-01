import os
import tempfile

import pytest

from modules.helper_funs import save_messages_from_person


class TestSaveMessagesFromPerson:
    def test_saves_messages_from_specified_person(self):
        data = {
            "messages": [
                {"sender_name": "Alice", "content": "Hello from Alice"},
                {"sender_name": "Bob", "content": "Hello from Bob"},
                {"sender_name": "Alice", "content": "Another from Alice"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_file = f.name

        try:
            save_messages_from_person(data, "Alice", output_file)

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            assert "Hello from Alice" in content
            assert "Another from Alice" in content
            assert "Hello from Bob" not in content
        finally:
            os.unlink(output_file)

    def test_handles_person_not_found(self):
        data = {
            "messages": [
                {"sender_name": "Alice", "content": "Hello"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_file = f.name

        try:
            save_messages_from_person(data, "NonExistent", output_file)

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            assert content == ""
        finally:
            os.unlink(output_file)

    def test_skips_messages_without_content(self):
        data = {
            "messages": [
                {"sender_name": "Alice", "content": "Has content"},
                {"sender_name": "Alice"},  # No content key
                {"sender_name": "Alice", "photos": []},  # No content key
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_file = f.name

        try:
            save_messages_from_person(data, "Alice", output_file)

            with open(output_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            assert "Has content" in lines[0]
        finally:
            os.unlink(output_file)

    def test_empty_messages(self):
        data = {"messages": []}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_file = f.name

        try:
            save_messages_from_person(data, "Alice", output_file)

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            assert content == ""
        finally:
            os.unlink(output_file)

    def test_preserves_unicode_characters(self):
        data = {
            "messages": [
                {"sender_name": "User", "content": "Zażółć gęślą jaźń"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_file = f.name

        try:
            save_messages_from_person(data, "User", output_file)

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            assert "Zażółć gęślą jaźń" in content
        finally:
            os.unlink(output_file)

    def test_each_message_on_new_line(self):
        data = {
            "messages": [
                {"sender_name": "User", "content": "Message 1"},
                {"sender_name": "User", "content": "Message 2"},
                {"sender_name": "User", "content": "Message 3"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_file = f.name

        try:
            save_messages_from_person(data, "User", output_file)

            with open(output_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 3
        finally:
            os.unlink(output_file)
