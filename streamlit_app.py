"""This is a very simple wrapper around the Streamlit UI code"""
import argparse

import streamlit as st

from arc.app.settings import Settings
from arc.app.ui import run_ui

st.set_page_config(layout="wide")  # type: ignore

parser = argparse.ArgumentParser(description="Select Streamlit mode")
parser.add_argument(
    "-p",
    default=Settings.default_pickle_id,
    type=str,
    help="Name of pickle file (excluding suffix)",
)
args = parser.parse_args()

run_ui(args.p)
