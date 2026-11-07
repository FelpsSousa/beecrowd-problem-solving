# 3484: Divided Class

## Link
https://judge.beecrowd.com/en/problems/view/3484

## Metadata

- Problem ID: 3484
- Platform: Beecrowd
- Category: Data Structures and Libraries
- Difficulty Level: 2
- Topics: Data Structures, Simulation
- Primary Language: C++
- Other Implementations: None
- Documentation Level: L2
- Status: In Progress
- Review Priority: Medium

## Summary
Given the order in which students arrive and their heights, build the class structure according to the problem rules, which correspond to inserting each height into a binary search tree. Then, for each level of the tree, print the minimum height found at that depth.

## My Interpretation
Each student becomes a node in a binary search tree:

- smaller height goes to the left
- greater height goes to the right

The first student becomes the root.  
The task is not to print the whole tree, but only the smallest height that appears at each depth.

## Core Idea
Build the binary search tree in the same order as the students arrive.

While inserting each new student, keep track of the current depth. As soon as the new node is placed, update the minimum value for that depth.

This avoids building the tree first and traversing it later just to compute per-level minima.

## Approach

1. Read `N` and the sequence of heights.
2. Insert the first height as the root at depth `0`.
3. For each next height:
   - walk through the tree as in a normal BST insertion
   - keep track of the current depth
   - insert the new node when an empty position is found
   - update the minimum height for that depth
4. Print all recorded levels from `0` to the deepest level reached.

## Why This Works
Each student is inserted exactly where the rules of the problem place them, which is precisely the insertion rule of a binary search tree.

Because every node belongs to exactly one depth, and because we update the minimum value of that depth when the node is inserted, the final array of minima correctly represents the smallest height at each level.

## Complexity

- Time: `O(N * h)`, where `h` is the height of the tree
- Worst case: `O(N^2)` when the tree becomes skewed
- Space: `O(N)`

Given that `N < 250`, this is more than enough.

## Implementation Notes

- **Ownership:** every node is owned by a `std::unique_ptr` and created with `std::make_unique`, so there is no `new` or `delete` and nothing can leak (C++ Core Guidelines R.11, R.20, R.23). When `root` goes out of scope, the whole tree is released automatically.
- **Insertion through the slot:** `insertStudent` walks a pointer to the owning `std::unique_ptr` itself (`std::unique_ptr<Node>* slot`), not to the node. When the loop stops, `slot` is the empty position, so the new node is written straight into it, with no parent pointer and no "was it left or right" check afterwards.
- **Destruction depth:** freeing the tree is recursive, one call per level. A skewed tree has depth `N - 1`, at most 248 here, which is safe. With hundreds of thousands of nodes, the tree would need an iterative teardown instead.
- **Answer during construction:** `minAtLevel` has `N` entries because a tree with `N` nodes is at most `N` levels deep, so `level` is always a valid index.

## Edge Cases

- only one student
- strictly increasing heights
- strictly decreasing heights
- mixed heights creating an unbalanced tree
- equal heights: the comparison is `height < current`, so an equal height goes to the right subtree
- the largest input (`N = 249`), which keeps the destruction depth and the `O(N^2)` worst case within limits

## What I Learned

- A binary search tree can be used directly from the problem statement, even when the statement is written in narrative form.
- Sometimes the best solution is to collect the required answer during insertion instead of performing an additional traversal later.
- A level-based answer does not always require BFS if the level is already known during construction.

## Implementations

- C++: `solutions/cpp/main.cpp`

## Status

- [ ] Solved
- [ ] Revisit later