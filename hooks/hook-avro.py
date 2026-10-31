"""Collect the avro.py transliterator resources, not Apache Avro RPC schemas."""
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("avro")
