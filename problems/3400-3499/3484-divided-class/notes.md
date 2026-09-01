# Notes

## What initially confused me
The statement describes the process as a playful queue-based activity, but the actual structure is a binary search tree built by insertion order.

## Mistakes to avoid

- forgetting that the first student is the root at depth `0`
- computing the answer from sorted values instead of tree levels
- mixing up "smaller goes left" and "greater goes right"
- overcomplicating the problem with a full traversal when insertion-time tracking is enough

## Pattern recognition
This is a binary search tree insertion problem with per-depth aggregation.

## Revisit trigger
Revisit this problem when reviewing:

- binary search trees
- tree depth
- insertion-based simulation
- collecting results during construction