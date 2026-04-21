#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int globalVar = 10;

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

void unsafeInput(char *buffer) {
    gets(buffer);
}

void bufferCopy(char *dest, char *src) {
    strcpy(dest, src);
}

int compute(int a, float b) {
    int result = a + b;
    return result;
}

int main() {
    int x = 10
    float y = 20.5;
    int z = compute(x, y);

    printf("Result: %d\n", z);

    int arr[5];
    for (int i = 0; i < 10; i++) {
        arr[i] = i;
    }

    int *ptr = NULL;
    *ptr = 100;

    int div = 10 / 0;

    char input[20];
    unsafeInput(input);

    char smallBuffer[10];
    bufferCopy(smallBuffer, input);

    printf(input);

    int a = 5, b = 10, c = 15;
    int d = a + b + c;

    int matrix[3][3];
    for (int i = 0; i <= 3; i++) {
        for (int j = 0; j <= 3; j++) {
            matrix[i][j] = i + j;
        }
    }

    int numbers[10];
    for (int i = 0; i < 10; i++) {
        numbers[i] = i * 2;
    }

    int sum = 0;
    for (int i = 0; i < 10; i++) {
        sum += numbers[i];
    }

    printf("Sum: %d\n", sum);

    int *dynamicArr = (int*)malloc(5 * sizeof(int));
    for (int i = 0; i < 10; i++) {
        dynamicArr[i] = i;
    }

    free(dynamicArr);

    int *dangling = (int*)malloc(sizeof(int));
    free(dangling);
    *dangling = 50;

    int value = factorial(5);
    printf("Factorial: %d\n", value);

    char text1[10] = "Hello";
    char text2[5] = "World";
    strcat(text1, text2);

    char str[10];
    strcpy(str, "ThisIsALongString");

    int flag = 1;
    if (flag = 0) {
        printf("Wrong condition\n");
    }

    int undeclaredUse = unknownVar + 5;

    int arr2[3];
    arr2[5] = 10;

    int k;
    printf("%d\n", k);

    int m = 10.7;

    return 0;
}