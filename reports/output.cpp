#include <iostream>

using namespace std;

int main() {
    bool t0;
    int limite = 3;
    int i = 0;
L0:;
    t0 = i < limite;
    if (!(t0)) goto L1;
    cout << "Vuelta completada" << endl;
    i = i + 1;
    goto L0;
L1:;
    return 0;
}