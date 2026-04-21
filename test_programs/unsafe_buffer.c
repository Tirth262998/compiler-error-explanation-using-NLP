#include <stdio.h>
#include <string.h>

int main() {
    char buffer[10];
    char* input = "This is a very long string that will overflow";
    strcpy(buffer, input);  // Unsafe!
    printf("Buffer: %s\n", buffer);
    return 0;
}
