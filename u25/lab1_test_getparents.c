#include "types.h"
#include "stat.h"
#include "user.h"

void test_no_fork();
void test_one_fork();
void test_two_forks();
void test_more_forks();

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf(1, "Usage: test_getparents <test_number>\n");
        exit();
    }

    int test_case = atoi(argv[1]);

    switch(test_case) {
        case 0:
            test_no_fork();
            break;
        case 1:
            test_one_fork();
            break;
        case 2:
            test_two_forks();
            break;
        case 3:
            test_more_forks();
            break;
        default:
            printf(1, "The argument is not correct!\n");
            exit();
    }

    exit();
}

// Test case 0
void test_no_fork() {
    getparents();  
}

// Test case 1
void test_one_fork() {
    int pid1;

    pid1 = fork();
    if (pid1 == 0) {
        getparents();
        exit();
    }

    wait();
}

// Test case 2
void test_two_forks() {
    int pid1, pid2;

    pid1 = fork();
    if (pid1 == 0) {
        pid2 = fork();
        if (pid2 == 0) {
            getparents();
            exit();
        }

        wait();

        exit();
    }

    wait();
}

// Test case 3 
void test_more_forks() {
    int pid1, pid2;

    pid1 = fork();
    if (pid1 == 0) {
        pid2 = fork();
        if (pid2 == 0) {
            fork();
            wait();
            getparents();
            sleep(1);
            exit();
        }

        wait();

        exit();
    }

    wait();
    exit();
}