#include <algorithm>
#include <iostream>
#include <memory>
#include <vector>

struct Node {
    int height;
    std::unique_ptr<Node> left;
    std::unique_ptr<Node> right;

    explicit Node(int h) : height(h) {}
};

// Walks down from the root following the problem's rule (shorter goes left,
// taller goes right) until it finds an empty slot, places the new node there
// and returns the depth of that slot.
int insertStudent(std::unique_ptr<Node>& root, int height) {
    std::unique_ptr<Node>* slot = &root;
    int level = 0;

    while (*slot) {
        slot = (height < (*slot)->height) ? &(*slot)->left : &(*slot)->right;
        ++level;
    }

    *slot = std::make_unique<Node>(height);
    return level;
}

int main() {
    int n;
    std::cin >> n;

    std::unique_ptr<Node> root;
    std::vector<int> minAtLevel(n, -1);  // -1 = level not reached yet
    int levelCount = 0;

    for (int i = 0; i < n; ++i) {
        int height;
        std::cin >> height;

        int level = insertStudent(root, height);

        // level <= i, because every insertion adds exactly one node, so the
        // index is always inside the vector of size n.
        if (minAtLevel[level] == -1 || height < minAtLevel[level]) {
            minAtLevel[level] = height;
        }
        levelCount = std::max(levelCount, level + 1);
    }

    for (int level = 0; level < levelCount; ++level) {
        std::cout << level << ' ' << minAtLevel[level] << '\n';
    }

    return 0;
}
