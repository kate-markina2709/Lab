#include <locale.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fstream>
#include <windows.h>
#include "Header.h"
#include <conio.h>
#include <iostream>
#include <string>
#include <sstream>
using namespace std;

unsigned long high, low;//high,low -левый и правый блоки
blowfish_ctx* ctx;

void swap(unsigned long* a, unsigned long* b)
{
	unsigned long temp;
	if (a && b) temp = *a, * a = *b, * b = temp;
}

//шифрующая функция
unsigned long F(blowfish_ctx* S, unsigned long x)
{
	return ((S->sbox[0][(x >> 24) & 0xFF] + S->sbox[1][(x >> 16) & 0xFF]) ^ S->sbox[2][(x >> 8) & 0xFF]) + S->sbox[3][(x) & 0xFF];
	// F(X1,X2,X3,X4)=(((S1[X1]+S2[X2])mod2^32 xor S3[X3])+S4[X4])mod2^32
}

//шифровка
void blowfish_encrypt_block(blowfish_ctx* ctx, unsigned long* high, unsigned long* low)
{
	int i;

	for (i = 0; i < 16; i++)	//шифрование 16 раундов
	{
		*high ^= ctx->P[i];	//XOR high с кючами P[i]
		*low ^= F(ctx, *high);	//XOR low и F(x)
		swap(low, high);	
	}

	swap(low, high);
	*low ^= ctx->P[16];	//17-й
	*high ^= ctx->P[17];//18-й
}

void blowfish_init(blowfish_ctx* ctx, unsigned char* key, size_t key_len)
{
	int i, j;
	unsigned long k, l;
	unsigned long long_key;

	if (ctx && key && key_len > 0)
	{
		memcpy(ctx->P, FIXED_P, 18 * sizeof(FIXED_P)); 

		for (i = 0; i < 4; i++)
			memcpy(ctx->sbox[i], FIXED_S[i], sizeof(FIXED_S[i])); 

		for (i = 0, k = 0; i < 18; i++)
		{
			for (j = 0, long_key = 0; j < 4; j++, k++) { 
				long_key = (long_key << 8) | key[k % key_len]; // сдвиг влево на 8 бит и побитовое ИЛИ с полученным числом
			}
			ctx->P[i] ^= long_key; 
		}

		for (i = 0, k = 0, l = 0; i < 18; i++) 
		{
			blowfish_encrypt_block(ctx, &k, &l);
			ctx->P[i] = k;
			ctx->P[++i] = l;
		} 

		for (i = 0; i < 4; i++)
		{
			for (j = 0; j < 256; j++)
			{
				blowfish_encrypt_block(ctx, &k, &l);
				ctx->sbox[i][j] = k;
				ctx->sbox[i][++j] = l;
			}
		}
	}
}

int main() {
	setlocale(LC_ALL, "Russian");
	system("chcp 1251");
	FILE* file1;
	fopen_s(&file1, "C:\\Users\\katem\\Desktop\\Дистанционка\\6 семестр\\безОС\\6 лр\\key.txt", "r");
	if (file1 == NULL) {
		cout << "err" << endl;
		return 0;
	}
	unsigned char key[255]; 
	size_t key_len = 0;
	SetConsoleCP(866);
	while (!feof(file1)) {
		key[key_len] = fgetc(file1);
		++key_len;
	}
	fclose(file1);
	--key_len;
	FILE* file2;
	fopen_s(&file2, "C:\\Users\\katem\\Desktop\\Дистанционка\\6 семестр\\безОС\\6 лр\\sms.txt", "r");
	if (file2 == NULL) {
		cout << "err" << endl;
		return 0;
	}
	char sms[255];
	size_t sms_len = 0;
	SetConsoleCP(866);
	while (!feof(file2)) {
		sms[sms_len] = fgetc(file2);
		++sms_len;
	}
	fclose(file2);
	ctx = (blowfish_ctx*)malloc(sizeof(blowfish_ctx));
	blowfish_init(ctx, key, key_len);
	int size = sms_len - 1;
	int mod = 0;
	mod = size % 8;
	if (mod != 0) {
		for (int i = 0; i < (8 - mod); ++i) {  
			sms[size + i] = ' ';
		}
		size = size + (8 - mod);
	}
	int i = 0, n = 0;
	char kod[256];
	while (i != size) {
		for (int j = 0; j < 4; ++j, ++i)
			high = (high << 8) | (unsigned char)(sms[i]); //перевод блока из 4х символов char в unsigned char и сдвигом по 8 бит переводим в unsigned long	
		for (int j = 0; j < 4; ++j, ++i)
			low = (low << 8) | (unsigned char)(sms[i]);
		blowfish_encrypt_block(ctx, &high, &low);
		for (int j = 3; j >= 0; --j) {
			kod[n] = ((char)((high >> (j * 8)) & 0xFF));
			++n;
		}
		for (int j = 3; j >= 0; --j) {
			kod[n] = ((char)((low >> (j * 8)) & 0xFF));
			++n;
		}
	}

	FILE* file3;
	fopen_s(&file3, "C:\\Users\\katem\\Desktop\\Дистанционка\\6 семестр\\безОС\\6 лр\\result.txt", "w+");
	if (file3 == NULL) {
		cout << "err" << endl;
		return 0;
	}
	SetConsoleCP(866);
	for (int j = 0; j < size; ++j) {
		fputc(kod[j], file3);
	}
	fclose(file3);
	delete(ctx);
}