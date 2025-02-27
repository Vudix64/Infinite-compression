import os
import pickle
import json
import tkinter as tk
from tkinter import filedialog, messagebox

# Constants
DATA_FILE = "data.pickle"  # File to store compression data
COMPRESSED_EXT = ".ctxt"  # Extension for compressed files

# Character set used for encoding
ALPHABET = (
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'abcdefghijklmnopqrstuvwxyz'
    '0123456789'
    '一丁七万丈三上下不与丑专且世丘丙业丛东丝丞丢两严並丧丨'
    'अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशसह़ािीुूृॅेैॉोौ्ॐक़ख़ग़ज़ड़ढ़फ़य़'
    'ლვთსმნაბჩცძწჭხჯჰჱჲჳჴჵჶჷჸჹჺᏣᏤᏥᏦᏧᏨᏩᏪᏫᏬᏭᏮᏯ'
)
ALPHABET = ''.join(sorted(set(ALPHABET)))[:256]  # Limit to 256 unique characters

# Function to convert an integer into a hash using the ALPHABET

def int_to_hash(n, length=5):
    base = len(ALPHABET)
    hash_str = []
    for _ in range(length):
        n, rem = divmod(n, base)
        hash_str.append(ALPHABET[rem])
    return ''.join(reversed(hash_str))

# Splits data into 2-bit blocks

def split_into_2bit_blocks(data):
    blocks = []
    for byte in data:
        blocks.append((byte >> 6) & 0x3)
        blocks.append((byte >> 4) & 0x3)
        blocks.append((byte >> 2) & 0x3)
        blocks.append(byte & 0x3)
    
    # Pad to make the length a multiple of 16
    while len(blocks) % 16 != 0:
        blocks.append(0)
    return blocks

# Reconstructs data from 2-bit blocks

def combine_from_2bit_blocks(blocks):
    data = []
    for i in range(0, len(blocks) - 3, 4):
        byte = (blocks[i] << 6) | (blocks[i+1] << 4) | (blocks[i+2] << 2) | blocks[i+3]
        data.append(byte)
    return data

# Compresses data using 4-level dictionary-based encoding

def compress(data, dictionary):
    current_data = split_into_2bit_blocks(data)

    for level in range(4):
        new_data = []
        for i in range(0, len(current_data), 2):
            pair = tuple(current_data[i:i+2])
            if pair not in dictionary[level]:
                hash_code = int_to_hash(len(dictionary[level]))
                dictionary[level][pair] = hash_code
            new_data.append(dictionary[level][pair])
        current_data = new_data

    compressed_str = ''.join(current_data)
    try:
        byte_data = bytes([ALPHABET.index(c) for c in compressed_str])
    except ValueError as e:
        raise ValueError(f"Symbol not found in ALPHABET: {str(e)}")
    return byte_data

# Decompresses data back to original form

def decompress(compressed_data, dictionary):
    try:
        compressed_str = ''.join([ALPHABET[byte] for byte in compressed_data])
    except IndexError as e:
        messagebox.showerror("Error", f"Invalid byte value in compressed data: {str(e)}")
        return []

    current_data = [compressed_str[i:i+5] for i in range(0, len(compressed_str), 5)]

    for level in reversed(range(4)):
        reverse_dict = {v: k for k, v in dictionary[level].items()}
        new_data = []
        for hash_code in current_data:
            if hash_code in reverse_dict:
                new_data.extend(reverse_dict[hash_code])
        current_data = new_data

    return combine_from_2bit_blocks(current_data)

# Saves dictionary and file data to a pickle file

def save_data_file(data):
    try:
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        messagebox.showerror("Error", f"Error saving data file: {str(e)}")

# Loads dictionary and file data from storage

def load_data_file():
    try:
        if os.path.exists("data.json"):
            with open("data.json", 'r') as f:
                data = json.load(f)
                data["dictionary"] = [{(tuple(k) if isinstance(k, list) else k): v for k, v in d.items()} for d in data["dictionary"]]
            os.remove("data.json")
            save_data_file(data)
            return data
        elif os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Error loading data file: {str(e)}")
        return {"dictionary": [{} for _ in range(4)], "files": []}
    return {"dictionary": [{} for _ in range(4)], "files": []}

# GUI Application class

class FileManager:
    def __init__(self, root):
        self.root = root
        self.root.title("4-Level Compressor")
        self.data = load_data_file()
        self.dictionary = self.data["dictionary"]

        self.listbox = tk.Listbox(self.root)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X)

        self.compress_btn = tk.Button(btn_frame, text="Compress", command=self.compress_file)
        self.compress_btn.pack(side=tk.LEFT, padx=5)

        self.decompress_btn = tk.Button(btn_frame, text="Decompress", command=self.decompress_file)
        self.decompress_btn.pack(side=tk.RIGHT, padx=5)

        self.update_list()

    def update_list(self):
        self.listbox.delete(0, tk.END)
        for fname in self.data["files"]:
            self.listbox.insert(tk.END, fname)

    def compress_file(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        try:
            with open(path, 'rb') as f:
                data = list(f.read())
        except Exception as e:
            messagebox.showerror("Error", f"Error reading file: {str(e)}")
            return

        try:
            compressed_data = compress(data, self.dictionary)
            output_name = os.path.basename(path) + COMPRESSED_EXT

            with open(output_name, 'wb') as f:
                f.write(compressed_data)

            if output_name not in self.data["files"]:
                self.data["files"].append(output_name)
                save_data_file(self.data)
                self.update_list()
            
            messagebox.showinfo("Success", "File compressed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Compression failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileManager(root)
    root.mainloop()
