cainixihuan: cainixihuan.o
	g++ -o cainixihuan cainixihuan.o
cainixihuan.o: cainixihuan.cpp
	g++ -c cainixihuan.cpp
clean:  
	rm -fr cainixihuan *.o
