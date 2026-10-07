#include <iostream>

int main() {
    // Only for large inputs (and say why in a comment):
    // std::ios::sync_with_stdio(false);
    // std::cin.tie(nullptr);

    int n;
    if (!(std::cin >> n)) {
        return 0;  // empty input
    }

    std::cout << n << '\n';
    return 0;
}
