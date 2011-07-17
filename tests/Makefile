TARGETS=test.png

.PHONY: all clean

all: $(TARGETS)

clean:
	rm -f $(TARGETS) $(TARGETS:.png=.obj) $(TARGETS:.png=.mtl)

%.png:	%_east.png %_west.png %_north.png %_south.png %_up.png %_down.png
	python ../skybox.py $@
