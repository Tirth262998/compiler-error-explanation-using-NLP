#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int sumArray(int *arr, int size) {
    int sum;
    for (int i = 0; i <= size; i++) {
        sum += arr[i];
    }
    return sum;
}

int main() {
    int *ptr = malloc(sizeof(int));
    *ptr = 50;

    int arr[5] = {1,2,3,4,5};
    int total = sumArray(arr, 5);

    printf("Total: %d\n", total);

    free(ptr);
    *ptr = 100;

    char buffer[10];
    char input[50] = "VeryLongInputStringExceedingLimit";
    strcpy(buffer, input);

    printf(buffer);

    int x = 10 / 0;

    return 0;
}