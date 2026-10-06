#include <stdio.h>

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 0; /* empty or malformed input */
    }

    printf("%d\n", n);
    return 0;
}
