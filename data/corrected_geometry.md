# Corrected walkable-area WKT for the Hermes 2009 bottleneck runs

Source: Liao et al. (2014), doi:10.1109/ITSC.2014.6957748: corridor 20 m wide centred on the
bottleneck, boards 1 m long (|y| < 0.5 in archive coordinates), gap centred at x = 0.9 with
width b_Exit. y extends 11 m in front of the boards (holding area, r = 8.618 m) and to the
archive's y = -8 behind them. Differences to the archive WKT: full corridor width instead of a
12 m box, walls closed to the sides, and gap widths equal to b_Exit (archive has 2.3/2.9/4.9).

## ao-240-400 (b_Exit = 2.4 m)

```
POLYGON ((10.9 0.5, 2.1 0.5, 2.1 -0.5, 10.9 -0.5, 10.9 -8, -9.1 -8, -9.1 -0.5, -0.3 -0.5, -0.3 0.5, -9.1 0.5, -9.1 11.5, 10.9 11.5, 10.9 0.5))
```

## ao-300-400 (b_Exit = 3.0 m)

```
POLYGON ((10.9 0.5, 2.4 0.5, 2.4 -0.5, 10.9 -0.5, 10.9 -8, -9.1 -8, -9.1 -0.5, -0.6 -0.5, -0.6 0.5, -9.1 0.5, -9.1 11.5, 10.9 11.5, 10.9 0.5))
```

## ao-360-400 (b_Exit = 3.6 m)

```
POLYGON ((10.9 0.5, 2.7 0.5, 2.7 -0.5, 10.9 -0.5, 10.9 -8, -9.1 -8, -9.1 -0.5, -0.9 -0.5, -0.9 0.5, -9.1 0.5, -9.1 11.5, 10.9 11.5, 10.9 0.5))
```

## ao-440-400 (b_Exit = 4.4 m)

```
POLYGON ((10.9 0.5, 3.1 0.5, 3.1 -0.5, 10.9 -0.5, 10.9 -8, -9.1 -8, -9.1 -0.5, -1.3 -0.5, -1.3 0.5, -9.1 0.5, -9.1 11.5, 10.9 11.5, 10.9 0.5))
```

## ao-500-400 (b_Exit = 5.0 m)

```
POLYGON ((10.9 0.5, 3.4 0.5, 3.4 -0.5, 10.9 -0.5, 10.9 -8, -9.1 -8, -9.1 -0.5, -1.6 -0.5, -1.6 0.5, -9.1 0.5, -9.1 11.5, 10.9 11.5, 10.9 0.5))
```

