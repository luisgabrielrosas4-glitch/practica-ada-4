#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <queue>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

struct Node {
    uint8_t ch;
    uint64_t freq;
    int min_symbol;
    uint64_t seq;
    shared_ptr<Node> left, right;
    Node(uint8_t c, uint64_t f, uint64_t s):ch(c),freq(f),min_symbol(c),seq(s){}
    Node(shared_ptr<Node> a,shared_ptr<Node> b,uint64_t s):ch(0),freq(a->freq+b->freq),min_symbol(min(a->min_symbol,b->min_symbol)),seq(s),left(a),right(b){}
    bool leaf()const{return !left&&!right;}
};
using Tree=shared_ptr<Node>;
struct Compare {
    bool operator()(const Tree&a,const Tree&b)const{
        if(a->freq!=b->freq)return a->freq>b->freq;
        if(a->min_symbol!=b->min_symbol)return a->min_symbol>b->min_symbol;
        return a->seq>b->seq;
    }
};
Tree build(const array<uint64_t,256>&counts){
    priority_queue<Tree,vector<Tree>,Compare>q;
    uint64_t seq=0;
    for(int i=0;i<256;i++)if(counts[i])q.push(make_shared<Node>((uint8_t)i,counts[i],seq++));
    while(q.size()>1){auto a=q.top();q.pop();auto b=q.top();q.pop();q.push(make_shared<Node>(a,b,seq++));}
    return q.empty()?nullptr:q.top();
}
class BitWriter {
    ostream& out;
    uint8_t current=0;
    unsigned used=0;
public:
    explicit BitWriter(ostream&s):out(s){}
    void bit(unsigned v){current=uint8_t((current<<1)|(v&1u));if(++used==8){out.put(char(current));current=0;used=0;}}
    void bits(const vector<uint8_t>&v){for(auto bit:v)this->bit(bit);}
    void align(){if(used){current=uint8_t(current<<(8-used));out.put(char(current));current=0;used=0;}}
};
class BitReader {
    istream& in;
    uint8_t current=0;
    unsigned remaining=0;
public:
    explicit BitReader(istream&s):in(s){}
    unsigned bit(){
        if(remaining==0){int c=in.get();if(c==char_traits<char>::eof())throw runtime_error("Archivo truncado");current=uint8_t(c);remaining=8;}
        unsigned result=(current>>(--remaining))&1u;
        return result;
    }
    void align(){remaining=0;}
};
void write_tree(const Tree&n,BitWriter&w){
    if(n->leaf()){
        w.bit(1);
        for(int i=7;i>=0;i--)w.bit((n->ch>>i)&1);
    }else{w.bit(0);write_tree(n->left,w);write_tree(n->right,w);}
}
Tree read_tree(BitReader&r,int&nodes){
    if(++nodes>511)throw runtime_error("Arbol invalido");
    if(r.bit()){
        uint8_t ch=0;
        for(int i=0;i<8;i++)ch=uint8_t((ch<<1)|r.bit());
        return make_shared<Node>(ch,0,(uint64_t)nodes);
    }
    auto a=read_tree(r,nodes),b=read_tree(r,nodes);
    return make_shared<Node>(a,b,(uint64_t)nodes);
}
void codes(const Tree&n,vector<uint8_t>&path,array<vector<uint8_t>,256>&table){
    if(n->leaf()){table[n->ch]=path;return;}
    path.push_back(0);codes(n->left,path,table);path.back()=1;codes(n->right,path,table);path.pop_back();
}
void put_u64(ostream&o,uint64_t n){for(int i=0;i<8;i++)o.put(char((n>>(8*i))&255u));}
uint64_t get_u64(istream&i){uint64_t v=0;for(int k=0;k<8;k++){int c=i.get();if(c==char_traits<char>::eof())throw runtime_error("Cabecera incompleta");v|=uint64_t(uint8_t(c))<<(8*k);}return v;}
array<uint64_t,256> count_bytes(const string&path,uint64_t&length){
    ifstream in(path,ios::binary);if(!in)throw runtime_error("No se puede abrir el archivo de entrada");
    array<uint64_t,256>freq{};array<char,65536>buf{};length=0;
    while(in){in.read(buf.data(),buf.size());auto n=in.gcount();length+=uint64_t(n);for(streamsize k=0;k<n;k++)freq[uint8_t(buf[size_t(k)])]++;}
    if(!in.eof())throw runtime_error("Error de lectura");
    return freq;
}
void encode(const string&src,const string&dst){
    if(src==dst)throw invalid_argument("Los archivos deben tener nombres distintos");
    uint64_t original=0;auto freq=count_bytes(src,original);Tree root=build(freq);
    ofstream out(dst,ios::binary|ios::trunc);if(!out)throw runtime_error("No se puede crear el destino");
    out.write("HUF1",4);put_u64(out,original);
    if(!root){if(!out)throw runtime_error("Fallo de escritura");return;}
    BitWriter tree_bits(out);write_tree(root,tree_bits);tree_bits.align();
    if(!root->leaf()){
        array<vector<uint8_t>,256>table;vector<uint8_t>path;codes(root,path,table);
        ifstream in(src,ios::binary);BitWriter writer(out);array<char,65536>buf{};
        while(in){in.read(buf.data(),buf.size());streamsize n=in.gcount();for(streamsize k=0;k<n;k++)writer.bits(table[uint8_t(buf[size_t(k)])]);}
        if(!in.eof())throw runtime_error("Error de lectura en segunda pasada");
        writer.align();
    }
    if(!out)throw runtime_error("Error al guardar archivo");
}
void decode(const string&src,const string&dst){
    if(src==dst)throw invalid_argument("Los archivos deben tener nombres distintos");
    ifstream in(src,ios::binary);if(!in)throw runtime_error("No se puede abrir el archivo comprimido");
    char magic[4];if(!in.read(magic,4)||string(magic,4)!="HUF1")throw runtime_error("Formato no valido");
    uint64_t count=get_u64(in);
    ofstream out(dst,ios::binary|ios::trunc);if(!out)throw runtime_error("No se puede crear el destino");
    if(count==0)return;
    BitReader bits(in);int nodes=0;Tree root=read_tree(bits,nodes);bits.align();
    if(root->leaf()){
        array<char,65536>buf;buf.fill(char(root->ch));
        while(count){auto n=uint64_t(min<uint64_t>(count,buf.size()));out.write(buf.data(),streamsize(n));count-=n;}
    }else{
        while(count--){auto n=root;while(!n->leaf())n=bits.bit()?n->right:n->left;out.put(char(n->ch));}
    }
    if(!out)throw runtime_error("Error al descomprimir");
}
int main(int argc,char**argv){
    if(argc!=4){cerr<<"Uso: huffman c|d entrada salida\n";return 2;}
    try{
        string mode=argv[1];
        if(mode=="c")encode(argv[2],argv[3]);
        else if(mode=="d")decode(argv[2],argv[3]);
        else throw invalid_argument("Modo invalido: c para comprimir, d para descomprimir");
    }catch(const exception&e){cerr<<e.what()<<'\n';return 1;}
}
