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

unsigned long high, low;
blowfish_ctx* ctx;

void swap(unsigned long* a, unsigned long* b)
{
	unsigned long temp;

	if (a && b)
		temp = *a, * a = *b, * b = temp;
}

//шифрующая функция
unsigned long F(blowfish_ctx* S, unsigned long x)
{
	return ((S->sbox[0][(x >> 24) & 0xFF] + S->sbox[1][(x >> 16) & 0xFF]) ^ S->sbox[2][(x >> 8) & 0xFF]) + S->sbox[3][(x) & 0xFF];
}


void blowfish_decrypt_block(blowfish_ctx* ctx, unsigned long* high, unsigned long* low)
{
	int i;

	for (i = 17; i > 1; i--)
	{
		*high ^= ctx->P[i];
		*low ^= F(ctx, *high);
		swap(low, high);
	}

	swap(low, high);
	*high ^= ctx->P[0];
	*low ^= ctx->P[1];
}
//шифровка
void blowfish_encrypt_block(blowfish_ctx* ctx, unsigned long* high, unsigned long* low)	//high,low - 
{	//левый и правый блоки
	int i;

	for (i = 0; i < 16; i++)	//шифрование 16 раундов
	{
		*high ^= ctx->P[i];	//XOR-им high с кючами P[i]
		*low ^= F(ctx, *high);	//XOR low и F(x)
		swap(low, high);	//Меняем местами
	}

	swap(low, high);
	*low ^= ctx->P[16];	//17-й
	*high ^= ctx->P[17];//и 18-й ключ XOR-ся с выходными блоками последнего раунда
}

//подготовка сети - xor двух матрич с ключом (расширение ключа)
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
				long_key = (long_key << 8) | key[k % key_len]; 
			}
			ctx->P[i] ^= long_key; 
		}

		for (i = 0, k = 0, l = 0; i < 18; i++) 
		{
			blowfish_encrypt_block(ctx, &k, &l);
			ctx->P[i] = k;
			ctx->P[++i] = l;
		}

		for (i = 0; i < 4; i++)// меняем все 4 S блока
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
	fopen_s(&file2, "C:\\Users\\katem\\Desktop\\Дистанционка\\6 семестр\\безОС\\6 лр\\result.txt", "r");
	if (file2 == NULL) {
		cout << "error" << endl;
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

	int i = 0, n = 0;
	char newsms[256];
	SetConsoleCP(866);
	while (i != size) {
		for (int j = 0; j < 4; ++j, ++i)
			high = (high << 8) | (unsigned char)(sms[i]); //перевод блока из 4х символов char в unsigned char и сдвигом по 8 бит переводим в unsigned long
		for (int j = 0; j < 4; ++j, ++i)
			low = (low << 8) | (unsigned char)(sms[i]);
		blowfish_decrypt_block(ctx, &high, &low);
		for (int j = 3; j >= 0; --j) {
			newsms[n] = ((char)((high >> (j * 8)) & 0xFF));
			++n;
		}
		for (int j = 3; j >= 0; --j) {
			newsms[n] = ((char)((low >> (j * 8)) & 0xFF));
			++n;
		}
	}

	int mod = 0;
	i = size - 1;
	while (newsms[i] == ' ' && i > 0) {
		++mod;
		--i;
	}

	FILE* file4;
	fopen_s(&file4, "C:\\Users\\katem\\Desktop\\Дистанционка\\6 семестр\\безОС\\6 лр\\result_desh.txt", "w+");
	if (file4 == NULL) {
		cout << "err" << endl;
		return 0;
	}
	for (int j = 0; j < size - mod; ++j) {
		fputc(newsms[j], file4);
	}
	fclose(file4);

	delete(ctx);
}