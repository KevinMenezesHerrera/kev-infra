volatile unsigned counter;
unsigned seed = 7;
int main(void) {
    counter = seed;
    for (;;) { counter++; }
}
