#include <stdio.h>
#include <stdlib.h>

int main() {
    int* ptr = malloc(sizeof(int));
    *ptr = 100;  // No null check!
    printf("Value: %d\n", *ptr);
    free(ptr);
    return 0;
}
