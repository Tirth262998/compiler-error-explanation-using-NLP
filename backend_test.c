#include <stdio.h>

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    int x = 5;
    float y = 3.14;
    int z = x + y;          /* implicit float-to-int */

    for (int i = 0; i < x; i++) {
        if (i % 2 == 0) {
            printf("even: %d\n", i);
        } else {
            printf("odd: %d\n", i);
        }
    }

    printf("factorial: %d\n", factorial(x));
    printf("z = %d\n", z);
    return 0               /* missing semicolon */
}