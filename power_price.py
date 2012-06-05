NORMAL = 'n'
SUMMER = 's'

ORI = 0
PH1 = 1
PH2 = 2

HOME = 0
BUSSINESS = 1 

h_origin = {NORMAL: [(110, 2.1), (220, 2.68), (170, 3.27), (200, 3.55), (9999999, 3.97)],
            SUMMER: [(110, 2.1), (220, 3.02), (170, 4.05), (200, 4.51), (9999999, 5.10)],}

h_phase1 = {NORMAL: [(120, 2.1), (210, 2.68), (170, 3.61), (200, 4.01), (9999999, 4.50)],
            SUMMER: [(120, 2.1), (210, 3.02), (170, 4.39), (200, 4.51), (9999999, 5.10)],}

h_phase2 = {NORMAL: [(120, 2.1), (210, 2.68), (170, 3.94), (200, 4.48), (9999999, 5.03)],
            SUMMER: [(120, 2.1), (210, 3.02), (170, 4.72), (200, 5.44), (9999999, 6.16)],}

b_origin = {NORMAL: [(330, 3.02), (170, 3.27), (200, 3.55), (9999999, 3.97)],
            SUMMER: [(330, 3.76), (170, 4.05), (200, 4.51), (9999999, 5.10)],}

b_phase1 = {NORMAL: [(330, 3.02), (370, 3.68), (800, 4.31), (9999999, 4.64)],
            SUMMER: [(330, 3.76), (370, 4.62), (800, 5.48), (9999999, 5.92)],}

b_phase2 = {NORMAL: [(330, 3.02), (370, 3.97), (800, 4.65), (9999999, 5.31)],
            SUMMER: [(330, 3.76), (370, 4.96), (800, 5.86), (9999999, 6.73)],}

GRID = {HOME: [h_origin, h_phase1, h_phase2],
        BUSSINESS: [b_origin, b_phase1, b_phase2],
        }

def deg2price(deg, charge_type, season, phase):
    price_list = GRID[int(charge_type)][int(phase)][season]
    price = 0
    formula = []
    for d, p in price_list:
        if deg <= 0:
            break
        d_phase = 2 * d
        if d_phase <= deg:
            deg = deg - d_phase
        else:
            d_phase = deg
            deg = 0
        formula.append((d_phase, p))
        price += float(d_phase) * p

    return price, formula

def price2deg(price, charge_type, season, phase):
    price_list = GRID[int(charge_type)][int(phase)][season]
    deg = 0
    formula = []
    price = float(price)
    for d, p in price_list:
        if price <= 0:
            break
        d_phase = d * 2
        p_phase = float(d_phase) * p
        if p_phase <= price:
            price = price - p_phase
        else:
            d_phase = price / p 
            price = 0
        formula.append((d_phase, p))
        deg += d_phase
    return deg, formula




