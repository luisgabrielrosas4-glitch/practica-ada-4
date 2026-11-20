#include <fstream>
#include <string>
#include <unordered_map>

void guardar_binario_como_texto(const std::string& entrada,
                               const std::string& salida,
                               const std::unordered_map<char,std::string>& codigos) {
    std::ifstream archivo(entrada, std::ios::binary);
    std::string bits;
    char caracter;
    while (archivo.get(caracter)) {
        bits += codigos.at(caracter);
    }
    std::ofstream destino(salida, std::ios::binary);
    destino << bits;
}
