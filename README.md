# Probabilistic Earley Parse

**Author:** Pratishtha Saxena

## Overview
This repository contains a Python implementation of a Probabilistic Earley Parse. The parse takes a Probabilistic Context-Free Grammar (PCFG) and an input sentence, applying the Earley algorithm to find all valid syntactic derivations. 

It utilizes Viterbi decoding (minimizing negative log probabilities, or weights) to resolve structural ambiguities and identify the most likely parse tree.

## Features
* **Viterbi Decoding:** Computes the probability of each derivation and guarantees the selection of the highest-probability parse.
* **LISP-Style Tree Formatting:** Reconstructs the best parse tree using detailed backpointers and outputs it in a deeply nested, mathematically aligned LISP format.
* **Span Extraction:** Explicitly tracks and outputs the `[NonTerminal, start_index, end_index]` constituency spans for every node in the winning tree.
* **Batch Processing:** Can automatically detect and run all grammar/sentence pairs in a directory if no specific files are provided.
* **Hash-Based Agenda:** Ensures $O(1)$ duplicate detection for chart items, maintaining optimal $O(n^3)$ time and $O(n^2)$ space complexity.

## Requirements
This script relies exclusively on Python standard libraries. No external dependencies are required.
* Python 3.x
* `sys`, `os`, `math`, `collections`

## Usage

### 1. Single File Mode
To parse a specific sentence file using a specific grammar file, pass them as command-line arguments:

```bash
python parse.py grammar_file.gr sentence_file.sen