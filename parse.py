import sys
import os
import math
from collections import defaultdict, deque

# -------------------------------
# Rule
# -------------------------------
class Rule:
    def __init__(self, lhs, rhs, prob):
        self.lhs = lhs
        self.rhs = rhs
        self.weight = -math.log(prob)

# -------------------------------
# State
# -------------------------------
class State:
    def __init__(self, lhs, rhs, dot, start):
        self.lhs = lhs
        self.rhs = rhs
        self.dot = dot
        self.start = start

    def is_complete(self):
        return self.dot == len(self.rhs)

    def next_symbol(self):
        return None if self.is_complete() else self.rhs[self.dot]

    def advance(self):
        return State(self.lhs, self.rhs, self.dot + 1, self.start)

    def key(self):
        return (self.lhs, tuple(self.rhs), self.dot, self.start)

    def __repr__(self):
        before = " ".join(self.rhs[:self.dot])
        after = " ".join(self.rhs[self.dot:])
        return f"{self.lhs} -> {before} • {after} [{self.start}]"

# -------------------------------
# Grammar Loader
# -------------------------------
def read_grammar(file):
    grammar = defaultdict(list)
    non_terminals = set()

    lines = []
    with open(file) as f:
        for line in f:
            if line.strip():
                lines.append(line.strip())

    for line in lines:
        parts = line.split()
        non_terminals.add(parts[1])

    for line in lines:
        parts = line.split()
        prob = float(parts[0])
        lhs = parts[1]
        rhs = parts[2:]
        grammar[lhs].append(Rule(lhs, rhs, prob))

    return grammar, non_terminals

# -------------------------------
# Earley Parser
# -------------------------------
def earley_parse(words, grammar, non_terminals):
    n = len(words)

    chart = [dict() for _ in range(n + 1)]
    backptr = [{} for _ in range(n + 1)]
    weight = [{} for _ in range(n + 1)]

    def add(i, state, w, bp=None):
        key = state.key()

        # Add if new, or update if we found a better (lower) weight
        if key not in chart[i] or weight[i][key] > w:
            chart[i][key] = state
            weight[i][key] = w
            backptr[i][key] = bp
            return True
        return False

    # Start
    start = State("γ", ["ROOT"], 0, 0)
    add(0, start, 0.0)

    for i in range(n + 1):
        agenda = deque(chart[i].values())

        while agenda:
            state = agenda.popleft()
            key = state.key()
            curr_w = weight[i][key]

            # ---------------- PREDICT ----------------
            if not state.is_complete():
                sym = state.next_symbol()

                if sym in non_terminals:
                    for rule in grammar[sym]:
                        new_state = State(rule.lhs, rule.rhs, 0, i)
                        if add(i, new_state, rule.weight):  # bp is None for predict
                            agenda.append(new_state)

                # ---------------- SCAN ----------------
                else:
                    if i < n and sym == words[i]:
                        new_state = state.advance()
                        # Store ('SCAN', previous_state_key, scanned_word)
                        add(i + 1, new_state, curr_w, ('SCAN', key, words[i]))

            # ---------------- COMPLETE ----------------
            else:
                for prev in list(chart[state.start].values()):
                    prev_key = prev.key()

                    if not prev.is_complete() and prev.next_symbol() == state.lhs:
                        new_state = prev.advance()
                        new_w = weight[state.start][prev_key] + curr_w
                        
                        # Store ('COMP', previous_state_key, completed_child_key, child_start_idx)
                        if add(i, new_state, new_w, ('COMP', prev_key, key, state.start)):
                            agenda.append(new_state)

    return chart, weight, backptr

# -------------------------------
# Tree & Span Extraction
# -------------------------------
def get_best_parse(chart, weight, backptr, n):
    best_w = float("inf")
    best_key = None

    for key, st in chart[n].items():
        if st.lhs == "γ" and st.is_complete() and st.start == 0:
            if weight[n][key] < best_w:
                best_w = weight[n][key]
                best_key = key

    if best_key is None:
        return None, float("inf"), []

    spans = []

    def build_node(key, end_idx):
        st = chart[end_idx][key]
        children = build_children(key, end_idx)

        # Skip the dummy γ node, just return its actual root child
        if st.lhs == "γ":
            return children[0]

        spans.append((st.lhs, st.start, end_idx))
        return (st.lhs, children)

    def build_children(key, end_idx):
        st = chart[end_idx][key]
        bp = backptr[end_idx].get(key)

        if st.dot == 0 or bp is None:
            return []

        if bp[0] == 'SCAN':
            _, prev_key, word = bp
            children = build_children(prev_key, end_idx - 1)
            children.append(word)
            return children

        elif bp[0] == 'COMP':
            _, prev_key, child_key, child_start = bp
            # Evaluate left side recursively
            children = build_children(prev_key, child_start)
            # Evaluate completed right child
            child_node = build_node(child_key, end_idx)
            children.append(child_node)
            return children

    tree = build_node(best_key, n)
    return tree, best_w, spans

# -------------------------------
# LISP-Style Tree Formatting
# -------------------------------
def format_lines(node):
    if isinstance(node, str):
        return [node]
    
    lhs, children = node
    
    # Base case for things like (Num 3)
    if len(children) == 1 and isinstance(children[0], str):
        return [f"({lhs} {children[0]})"]

    prefix = f"({lhs} "
    indent = len(prefix)

    lines = []
    for i, child in enumerate(children):
        child_lines = format_lines(child)
        if i == 0:
            lines.append(prefix + child_lines[0])
            for line in child_lines[1:]:
                lines.append(" " * indent + line)
        else:
            for line in child_lines:
                lines.append(" " * indent + line)

    # Attach closing parenthesis to the very last line
    lines[-1] = lines[-1] + ")"
    return lines

def print_tree(tree):
    lines = format_lines(tree)
    print("\n".join(lines))

# -------------------------------
# Runner
# -------------------------------
def run_parser(gr, sen):
    grammar, non_terminals = read_grammar(gr)

    with open(sen) as f:
        for line in f:
            sent = line.strip()
            if not sent:
                continue

            words = sent.split()
            chart, weight, backptr = earley_parse(words, grammar, non_terminals)
            tree, best_w, spans = get_best_parse(chart, weight, backptr, len(words))

            if tree is not None:
                # Print tree in instructor format
                print_tree(tree)
                
                # Print Negative Log Probability (Weight) exactly as instructor requested
                print(best_w)
                
                # Print raw probability (for Q2)
                prob = math.exp(-best_w)
                print(prob)
                
                # Print Constituency Spans (sorted logically by start, then end index)
                spans.sort(key=lambda x: (x[1], x[2]))
                for span in spans:
                    print(f"[{span[0]}, {span[1]}, {span[2]}]")
            else:
                print("NONE")

# -------------------------------
# Main
# -------------------------------
def main():
    if len(sys.argv) >= 3:
        run_parser(sys.argv[1], sys.argv[2])
        return

    files = os.listdir()
    for f in sorted(files):
        if f.endswith(".gr"):
            sen = f.replace(".gr", ".sen")
            if sen in files:
                run_parser(f, sen)

if __name__ == "__main__":
    main()