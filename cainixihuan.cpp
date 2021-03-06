#include<iostream>  
#include<fstream>  
#include<stdio.h>  
#include<map>  
#include<set>  
#include<vector>  
#include<cstdlib>  
#include<cmath>  
#include<cstring>  
#include<algorithm> 
#include <sstream>

using namespace std;

typedef struct
{
	int uid;
	int iid;
}UIDIID;

bool operator < (const UIDIID &ui1, const UIDIID &ui2)
{
	if (ui1.uid < ui2.uid)
	{
		return true;
	}
	else
	{
		return false;
	}
}

class CSVRow
{
	public:
		std::string const& operator[](std::size_t index) const
		{
			return m_data[index];
		}
		std::size_t size() const
		{
			return m_data.size();
		}
		void readNextRow(std::istream& str)
		{
			std::string         line;
			std::getline(str, line);

			std::stringstream   lineStream(line);
			std::string         cell;

			m_data.clear();
			while(std::getline(lineStream, cell, ','))
			{
				m_data.push_back(cell);
			}
			// This checks for a trailing comma with no data after it.
			if (!lineStream && cell.empty())
			{
				// If there was a trailing comma then add an empty element.
				m_data.push_back("");
			}
		}
	private:
		std::vector<std::string>    m_data;
};

std::istream& operator>>(std::istream& str, CSVRow& data)
{
	data.readNextRow(str);
	return str;
}

class CSVIterator
{
	public:
		typedef std::input_iterator_tag     iterator_category;
		typedef CSVRow                      value_type;
		typedef std::size_t                 difference_type;
		typedef CSVRow*                     pointer;
		typedef CSVRow&                     reference;

		CSVIterator(std::istream& str)  :m_str(str.good()?&str:NULL) { ++(*this); }
		CSVIterator()                   :m_str(NULL) {}

		// Pre Increment
		CSVIterator& operator++()               {if (m_str) { if (!((*m_str) >> m_row)){m_str = NULL;}}return *this;}
		// Post increment
		CSVIterator operator++(int)             {CSVIterator    tmp(*this);++(*this);return tmp;}
		CSVRow const& operator*()   const       {return m_row;}
		CSVRow const* operator->()  const       {return &m_row;}

		bool operator==(CSVIterator const& rhs) {return ((this == &rhs) || ((this->m_str == NULL) && (rhs.m_str == NULL)));}
		bool operator!=(CSVIterator const& rhs) {return !((*this) == rhs);}
	private:
		std::istream*       m_str;
		CSVRow              m_row;
};

#define MAXLEN 256

int main(int argc, char *argv[])
{
	map<UIDIID, unsigned char> mapUidIidScores;
	char trainFileName[MAXLEN] = {0};
	strncpy(trainFileName, "../train.csv", MAXLEN - 1);
	if (argc > 1)
	{
		strncpy(trainFileName, argv[1], MAXLEN - 1);
	}

	std::ifstream fin(trainFileName);

	UIDIID tmp = {0};
	//生成(uid, iid)与score的map
	for(CSVIterator loop(fin); loop != CSVIterator(); ++loop)
	{
		tmp.uid = atoi((*loop)[0].c_str());
		tmp.iid = atoi((*loop)[1].c_str());
		mapUidIidScores[tmp] = (char)atoi((*loop)[2].c_str());
		printf("uid %d, iid %d, score %d\n", tmp.uid, tmp.iid, mapUidIidScores[tmp]);
	}
	return 0;
}

