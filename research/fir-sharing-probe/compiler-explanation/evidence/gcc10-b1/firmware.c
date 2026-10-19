#define BLOCK 1
#define SAMPLES 257
#include "kernel.h"
static const int16_t input_data[SAMPLES]={-1024,1023,0,-1,1,-1023,1022,-261,-687,437,-11,811,-203,-839,277,850,907,-556,653,476,830,1015,-618,-225,777,-466,-147,26,-714,93,217,160,-956,542,-267,328,241,66,717,147,620,-289,400,492,-505,376,982,-928,-98,-891,29,-219,18,-231,-900,-307,408,418,-943,239,-68,855,170,-44,-113,561,491,510,860,-609,616,-39,-261,356,1000,461,379,268,-985,716,46,-651,-307,101,792,54,1006,368,-636,-139,494,-421,-574,-646,826,-943,-803,-912,822,848,998,-660,-80,914,181,741,756,-801,1,-593,-674,-216,527,-226,319,219,-957,-788,-138,65,115,-1000,976,-339,145,1022,-266,-920,288,-81,-793,897,-993,-250,208,262,368,218,430,460,50,375,-576,642,179,-982,566,950,470,-97,-27,-460,-29,-313,-634,833,547,455,225,525,976,-173,-290,-862,769,-613,927,-915,5,-881,983,-380,68,-509,127,414,-651,-517,-376,761,-564,754,550,-142,525,-189,-231,-535,477,-814,52,141,-387,-29,-220,204,954,571,649,-203,183,344,481,-590,319,-703,-348,-234,-819,-413,-285,-628,171,720,-880,-384,712,-365,72,797,-38,-597,-183,-23,290,748,-547,-69,866,404,646,-796,576,-1008,-770,301,172,-1015,-224,-934,-733,-986,911,-345,322,293,595,-763,-511,826,-837,882,52,-200,360,-490,-384};
static struct { uint64_t lo; ProbeState state; uint64_t hi; } storage;
static int16_t source[SAMPLES];
static int16_t destination[SAMPLES+4];
extern void measured(void);
void process_stream(void) {
 for(uint32_t off=0;off<SAMPLES;off+=BLOCK) {
  uint32_t b=SAMPLES-off; if(b>BLOCK)b=BLOCK;
  probe_process(&storage.state,source+off,destination+2+off,b);
 }
}
static void put(char c){*(volatile uint32_t*)0xe0000000=(uint32_t)c;}
static void hex32(uint32_t v){for(int s=28;s>=0;s-=4){unsigned d=(v>>s)&15;put(d<10?'0'+d:'a'+d-10);}}
static void hex16(int16_t v){uint32_t u=(uint16_t)v;for(int s=12;s>=0;s-=4){unsigned d=(u>>s)&15;put(d<10?'0'+d:'a'+d-10);}}
int main(void) {
 for(unsigned i=0;i<SAMPLES;++i)source[i]=input_data[i];
 probe_init(&storage.state); storage.lo=storage.hi=0x5a5a5a5a5a5a5a5aULL;
 destination[0]=destination[1]=destination[SAMPLES+2]=destination[SAMPLES+3]=23130;
 measured(); put('O');put(':');for(unsigned i=0;i<SAMPLES;++i)hex16(destination[i+2]);put('\n');
 put('H');put(':');for(unsigned i=0;i<TAPS-1;++i){uint64_t v=(uint64_t)probe_get_state(&storage.state,i);hex32((uint32_t)(v>>32));hex32((uint32_t)v);}put('\n');
 put('G');put(':');hex32((uint32_t)storage.lo);hex32((uint32_t)(storage.lo>>32));hex32((uint32_t)storage.hi);hex32((uint32_t)(storage.hi>>32));
 hex16(destination[0]);hex16(destination[1]);hex16(destination[SAMPLES+2]);hex16(destination[SAMPLES+3]);put('\n');
 put('M');put(':');hex32(probe_state_bytes());put('\n');return 0;
}
