#define PIN_DIN 23
#define PIN_CLK 18
#define PIN_CS  5
#define NUM_DEVICES 2

#include <LedControl.h>

LedControl lc = LedControl(PIN_DIN, PIN_CLK, PIN_CS, NUM_DEVICES);

#define Matrix_Width 8
#define Matrix_Heigth 8
#define PIN_Tilt 5

#define LedMatrixAttached 1
#define Speedup 0

bool top[Matrix_Width][Matrix_Heigth];
bool bottom[Matrix_Width][Matrix_Heigth];

enum Orientations
{
  TopBottom = 0,
  BottomTop = 1
} orientation = TopBottom;

typedef enum {
  Top = 0,
  Bottom = 1
} Glass;

const int maxIterations = 513;
int counter = 0;
int blinkCounter = 0;
unsigned long startTime = 0;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

void setup() {
  Serial.begin(115200);  
  pinMode(PIN_Tilt, INPUT_PULLUP);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  randomSeed(analogRead(0));

  SetupMatrix();
}

void loop() {  
  PhysicLoop();  
}

void SetupMatrix() {
  for (int index = 0; index < lc.getDeviceCount(); index++) {
    lc.shutdown(index, false);
    lc.setIntensity(index, 2);
    lc.clearDisplay(index);
  }
  orientation = (digitalRead(PIN_Tilt) > 0) ? BottomTop : TopBottom;
  CheckTilt();
  ResetMatrix();
}

void ResetMatrix() {  
  SetAll(GetGlass(Top), orientation == TopBottom);
  SetAll(GetGlass(Bottom), orientation == BottomTop);
  counter = 0;
  startTime = 0;
  blinkCounter = 0;
}

void PhysicLoop() {
  CheckTilt();

  if (startTime == 0)
    startTime = millis();

  if (counter >= maxIterations + 1) {
    EndBlink();
    return;
  } else {
    counter++;
  }

  bool topTick = IterateRows(Top);
  bool bottomTick = IterateRows(Bottom);
  bool transferGrain;
  if (!topTick && !bottomTick)
    transferGrain = TransferPixel();

  if (!topTick && !bottomTick && !transferGrain) {
    EndClock();
    return;
  }

#if !LedMatrixAttached
  Print();
#endif

  if (CheckGlasses())
    counter = 1000;

#if Speedup
  delay(100);
  return;
#endif

  // Dynamically calculate delay per iteration
  unsigned long iterationDelay = targetDuration / maxIterations;
  delay(iterationDelay);
}


bool TransferPixel() {
  bool topValue = GetValue(Top, Matrix_Width + Matrix_Heigth - 2, 0);
  bool bottomValue = GetValue(Bottom, 0, 0);

  if (topValue && !bottomValue)
    CopyPixel(Top, Matrix_Width + Matrix_Heigth - 2, 0, Bottom, 0, 0);
  return topValue && !bottomValue;
}

bool IterateRows(uint8_t glass) {
  bool prevLineHasValues = false;
  for (uint8_t i = 0; i < Matrix_Heigth + Matrix_Width - 1; i++) {
    bool lineFilled = IsLineFilled(glass, i);
    bool lineHasGaps = lineFilled ? HasLineGap(glass, i) : true;
    bool nextLineHasGaps = i < Matrix_Heigth + Matrix_Width - 1 ? HasLineGap(glass, i + 1) : false;
    bool ticked = false;

    if (prevLineHasValues && lineHasGaps)
      ticked = FillGapFromAbove(glass, i);
    if (lineFilled && lineHasGaps && nextLineHasGaps)
      ticked = FillGapBelow(glass, i);
    //only one tick per iteration
    if (ticked)
      return true;
    prevLineHasValues = lineFilled;
  }
  return false;
}

bool FillGapFromAbove(uint8_t glass, uint8_t row) {

  uint8_t columns[Matrix_Width];
  uint8_t NoOfColums = GetRow(row - 1, columns);
  uint8_t colPrev;

  NoOfColums = GetRow(row, columns);
  uint8_t colCurr;
  for (colCurr = 0; colCurr < NoOfColums; colCurr++) {
    bool value = GetValue(glass, row, colCurr);
    if (!value)
      break;
  }

  colPrev = GetNextPixel(glass, row - 1, row, colCurr, true);

  CopyPixel(glass, row - 1, colPrev, glass, row, colCurr);
  return true;
}

bool FillGapBelow(uint8_t glass, uint8_t row) {

  uint8_t columns[Matrix_Width];
  uint8_t NoOfColums = GetRow(row + 1, columns);
  uint8_t colNext;
  uint8_t colCurr;

  NoOfColums = GetRow(row, columns);
  for (colCurr = 0; colCurr < NoOfColums; colCurr++)
    if (GetValue(glass, row, colCurr))
      break;

  colNext = GetNextPixel(glass, row + 1, row, colCurr, false);

  //Line below already full:
  if (GetValue(glass, row + 1, colNext))
    return false;
  CopyPixel(glass, row, colCurr, glass, row + 1, colNext);
  return true;
}

bool IsLineFilled(uint8_t glass, uint8_t row) {
  uint8_t columns[Matrix_Width];
  uint8_t NoOfColums = GetRow(row, columns);
  for (uint8_t i = 0; i < NoOfColums; i++) {
    bool value = GetValue(glass, row, i);
    if (value)
      return true;
  }
  return false;
}

bool HasLineGap(uint8_t glass, uint8_t row) {
  uint8_t columns[Matrix_Width];
  uint8_t NoOfColums = GetRow(row, columns);
  for (uint8_t i = 0; i < NoOfColums; i++) {
    bool value = GetValue(glass, row, i);
    if (!value)
      return true;
  }
  return false;
}

uint8_t GetGlass(uint8_t glass) {
  if (orientation == TopBottom)
    return glass == Top ? 0 : 1;
  return glass == Top ? 1 : 0;
}

void Print() {
  PrintMatrix(Top);
  PrintMatrix(Bottom);
}

void PrintMatrix(uint8_t glass) {
  uint8_t no = GetGlass(glass);
  switch (no) {
    case 0:
      PrintArray(top);
      break;
    case 1:
      PrintArray(bottom);
      break;
  }
}

void PrintArray(bool arr[Matrix_Heigth][Matrix_Width]) {
  for (int i = 0; i < Matrix_Heigth + Matrix_Width - 1; i++) {
    int startRow = max(0, i - Matrix_Width + 1);
    int startCol = min(i, Matrix_Width - 1);
    int numElements = min(i + 1, Matrix_Heigth - startRow);
    for (uint8_t space = 0; space < Matrix_Width - numElements; space++)
      Serial.print(" ");
    for (int j = 0; j < numElements; j++) {
      int x = startRow + j;
      int y = startCol - j;
      int value = arr[x][y];
      Serial.print(value ? "X" : "0");
      Serial.print(" ");
    }
    Serial.println();
  }
}

void SetAll(uint8_t glass, bool state) {
  for (int y = 0; y < Matrix_Heigth; y++)
    for (int x = 0; x < Matrix_Width; x++)
      SetPixelByCoordinates(glass, x, y, state);
}

void CopyPixel(uint8_t glassFrom, uint8_t rowFrom, uint8_t colFrom, uint8_t glassTo, uint8_t rowTo, uint8_t colTo) {
  bool state = GetValue(glassFrom, rowFrom, colFrom);
  SetPixel(glassFrom, rowFrom, colFrom, !state);
  SetPixel(glassTo, rowTo, colTo, state);
}

void CopyPixelByCoordinates(uint8_t glassFrom, uint8_t xFrom, uint8_t yFrom, uint8_t glassTo, uint8_t xTo, uint8_t yTo) {
  SetPixelByCoordinates(glassFrom, xFrom, yFrom, false);
  SetPixelByCoordinates(glassTo, xTo, yTo, true);
}

void SetPixel(uint8_t glass, uint8_t row, uint8_t col, bool state) {
  uint8_t x;
  uint8_t y;
  GetCoordinates(row, col, x, y);
  SetPixelByCoordinates(glass, x, y, state);
}
void SetPixelByCoordinates(uint8_t glass, uint8_t x, uint8_t y, bool state) {
  uint8_t glassId = GetGlass(glass);
  
  switch (glassId) {
    case 0:
      top[x][y] = state;
      break;
    case 1:
      bottom[x][y] = state;
      break;
  }
  //Invert matrixes...
  lc.setLed(glassId ? 0 : 1, x, y, state);
}

void GetCoordinates(uint8_t row, uint8_t col, uint8_t& x, uint8_t& y) {
  if (orientation == BottomTop)
    row = (Matrix_Width + Matrix_Heigth - 2) - row;

  int startRow = max(0, row - Matrix_Width + 1);
  int startCol = min(row, Matrix_Width - 1);
  int numElements = min(row + 1, Matrix_Heigth - startRow);
  x = startRow + col;
  y = startCol - col;
}

void PrintPixel(uint8_t glass, uint8_t row, uint8_t col) {
  uint8_t x;
  uint8_t y;
  GetCoordinates(row, col, x, y);
  bool value;
  switch (GetGlass(glass)) {
    case 0:
      value = top[x][y];
      break;
    case 1:
      value = bottom[x][y];
      break;
  }
  Serial.print(value ? "X" : "0");
  Serial.print(" (" + String(row));
  Serial.print("/" + String(col));
  Serial.print(") [" + String(x));
  Serial.print("," + String(y));
  Serial.print("]");
  Serial.print(" " + String(GetLedNo(x, y)));
  Serial.print(" ");
}

uint8_t GetLedNo(uint8_t x, uint8_t y) {
  return x + y * Matrix_Width;
}

uint8_t GetRow(uint8_t rowNo, uint8_t *columns) {
  if (orientation == BottomTop)
    rowNo = (Matrix_Width + Matrix_Heigth - 2) - rowNo;

  uint8_t c = 0;
  int startRow = max(0, rowNo - Matrix_Width + 1);
  int startCol = min(rowNo, Matrix_Width - 1);
  int numElements = min(rowNo + 1, Matrix_Heigth - startRow);
  for (int j = 0; j < numElements; j++) {
    int row = startRow + j;
    int col = startCol - j;
    columns[c++] = col;
  }
  if (c <= Matrix_Width - 1)
    columns[c] = 255;
  return numElements;
}
uint8_t GetNextPixel(uint8_t glass, uint8_t rowTo, uint8_t rowFrom, uint8_t colFrom, bool state) {
  uint8_t colTo = 0;
  uint8_t columns[Matrix_Width];
  uint8_t NoOfPrevColumns = GetRow(rowFrom, columns);
  uint8_t NoOfColumns = GetRow(rowTo, columns);

  if (NoOfColumns <= 1)
    return colTo;

  //X 0
  // 0
  if (NoOfColumns < NoOfPrevColumns) {
    if (colFrom == 0)
      colTo = 0;
    else if (colFrom >= NoOfColumns - 1)
      colTo = NoOfColumns - 1;
    else
      colTo = random(colFrom - 1, colFrom + 1);
  }

  // 0 0
  //X 0 0
  if (NoOfColumns > NoOfPrevColumns) {
    colTo = random(colFrom, colFrom + 2);
  }

  if (GetValue(glass, rowTo, colTo) == state)
    return colTo;

  if (colFrom > NoOfColumns - 1)
    colFrom = NoOfColumns - 1;
  if (random(0, 2) == 1) {
    //Next
    for (colTo = colFrom; colTo < NoOfColumns; colTo++)
      if (GetValue(glass, rowTo, colTo) == state)
        return colTo;
  } else {
    //Prev
    for (colTo = colFrom; colTo > 0; colTo--)
      if (GetValue(glass, rowTo, colTo) == state)
        return colTo;
  }

  //Fallback:
  for (colTo = 0; colTo < NoOfColumns; colTo++)
    if (GetValue(glass, rowTo, colTo) == state)
      return colTo;

  return colTo;
}
bool GetValue(uint8_t glass, uint8_t row, uint8_t col) {
  uint8_t x;
  uint8_t y;
  GetCoordinates(row, col, x, y);
  return GetValueByCoordinates(glass, x, y);
}
bool GetValueByCoordinates(uint8_t glass, uint8_t x, uint8_t y) {
  switch (GetGlass(glass)) {
    case 0:
      return top[x][y];
      break;
    case 1:
      return bottom[x][y];
      break;
  }
}

void CheckTilt() {
  int tiltValue = digitalRead(PIN_Tilt);
  if((orientation == TopBottom ? LOW : HIGH) == tiltValue){
    lastDebounceTime = millis();
    return;
  }
  if ((millis() - lastDebounceTime) > debounceDelay)
    orientation = tiltValue;
  else
    return;
  
  digitalWrite(LED_BUILTIN, orientation == TopBottom ? LOW : HIGH);
  Serial.println(orientation == TopBottom ? "Top Bottom" : "Bottom Top");
  //change counter:
  if(counter > 0 && counter < maxIterations)
    counter = maxIterations - counter;
  if (counter >= 1000)
    SetupMatrix();
}

bool CheckGlasses() {
  uint8_t topCounter = 0;
  uint8_t bottomCounter = 0;
  for (uint8_t glass = 0; glass <= 1; glass++)
    for (int y = 0; y < Matrix_Heigth; y++)
      for (int x = 0; x < Matrix_Width; x++)
        if (GetValueByCoordinates(glass, x, y))
          glass == 0 ? topCounter++ : bottomCounter++;
  if (topCounter + bottomCounter != Matrix_Heigth * Matrix_Width) {
    Serial.println("Failed!");
    Serial.println("Top: " + String(topCounter));
    Serial.println("Bottom: " + String(bottomCounter));
    Serial.println("Counter: " + String(counter));
    return true;
  }
  return false;
}
void EndClock() {
  
