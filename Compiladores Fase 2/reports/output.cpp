#include <iostream>
#include <string>

using namespace std;

int suma(int a, int b) {
    int resultado = (a + b);
    return resultado;
}

int main() {
    int x = 10;
    int y = 5;
    int total = suma(x, y);
    if ((total > 10)) {
        cout << total << endl;
    } else {
        cout << y << endl;
    }
    while ((x != 0)) {
        x = (x - 1);
    }
    for (int i = 0; (i < 3); i++) {
        cout << i << endl;
    }
    return 0;
}