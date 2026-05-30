
import csv, io

raw = [
(1,"gopfan2",350530,4600000,7.6,"Multi-Wallet,Sharp Selector"),
(2,"aenews2",288120,10087862,2.9,"Multi-Wallet,Volume Whale"),
(3,"ColdMath",131190,10578505,1.2,"Volume Whale,Swing Trader"),
(4,"gopfan",118426,739900,16.0,"Multi-Wallet,Sharp Selector"),
(5,"bama124",86600,410556,21.1,"Sharp Selector"),
(6,"Hans323",81109,7109443,1.1,"Volume Whale,Swing Trader"),
(7,"Handsanitizer23",71174,953274,7.5,"Sharp Selector"),
(8,"Poligarch",69372,8897276,0.78,"Volume Whale,Swing Trader"),
(9,"automatedAItradingbot",64894,2566237,2.5,"Bot/Algo"),
(10,"BeefSlayer",64270,1468616,4.4,"Sharp Selector,Swing Trader"),
(11,"BigMike11",62776,850755,7.4,"Sharp Selector"),
(12,"HondaCivic",59188,7409853,0.8,"Multi-Wallet,Volume Whale"),
(13,"Kapii",57190,1833451,3.1,"Sharp Selector,Swing Trader"),
(14,"WeatherTraderBot",57179,1788233,3.2,"Bot/Algo"),
(15,"aenews-915",55093,598139,9.2,"Multi-Wallet,Sharp Selector"),
(16,"russell110320",54356,1441162,3.8,"Swing Trader"),
(17,"junkbonds",51403,864486,5.9,"Sharp Selector"),
(18,"CoffeeLover",51105,161054,31.7,"Sharp Selector"),
(19,"chilling",50781,741105,6.9,"Sharp Selector,Multi-Wallet"),
(20,"maskache2",49008,5050549,1.0,"Multi-Wallet,Volume Whale"),
(21,"JoeTheMeteorologist",46777,2702811,1.7,"Domain Expert"),
(22,"HenryTheAtmoPhD",46186,3464306,1.3,"Domain Expert"),
(23,"aboss",38787,1074084,3.6,"Swing Trader"),
(24,"Protrade2",37717,1661107,2.3,"Multi-Wallet,Swing Trader"),
(25,"9985",37107,385980,9.6,"Sharp Selector"),
(26,"ANudeEgg",36270,279088,13.0,"Sharp Selector"),
(27,"protrade3",35771,1798593,2.0,"Multi-Wallet,Swing Trader"),
(28,"Shoemaker34",33958,511511,6.6,"Swing Trader"),
(29,"1-800-LIQUIDITY",33506,908899,3.7,"Swing Trader"),
(30,"neobrother",32301,1849193,1.7,"Swing Trader"),
(31,"NoonienSoong",31479,5587217,0.56,"Volume Whale,Swing Trader"),
(32,"Lavincey",31297,2169913,1.4,"Swing Trader"),
(33,"Ooookey",31157,2907536,1.1,"Volume Whale,Swing Trader"),
(34,"opopv",30808,2481682,1.2,"Swing Trader,Volume Whale"),
(35,"Nowhere-Man",30410,971806,3.1,"Sharp Selector"),
(36,"khalidakup",29585,1994067,1.5,"Swing Trader"),
(37,"meropi",28137,6917998,0.41,"Volume Whale,Swing Trader"),
(38,"jangsunjuu",27981,721440,3.9,"Sharp Selector"),
(39,"387411007415611814092217897387",27189,2777293,1.0,"Bot/Algo"),
(40,"0xf2e346ab",26543,1144077,2.3,"Swing Trader"),
(41,"Railbird",25428,970772,2.6,"Sharp Selector"),
(42,"jfm-20",24938,638000,3.9,"Swing Trader"),
(43,"EngineOfHondaCivic",24475,1523216,1.6,"Multi-Wallet,Swing Trader"),
(44,"strider2",23947,275689,8.7,"Sharp Selector"),
(45,"Weatherstappen",23620,1154940,2.0,"Domain Expert,Swing Trader"),
(46,"Hoaqin",23384,427054,5.5,"Sharp Selector"),
(47,"David32534",22945,345269,6.6,"Sharp Selector"),
(48,"Brokie",22597,351115,6.4,"Sharp Selector"),
(49,"Junhoo2",21988,342192,6.4,"Sharp Selector"),
(50,"vip68",21940,2397681,0.91,"Volume Whale,Swing Trader"),
(51,"Cucurella",21890,379174,5.8,"Sharp Selector"),
(52,"DarbySkees",21458,42915,50.0,"Sharp Selector"),
(53,"MrFox",21382,113878,18.8,"Sharp Selector"),
(54,"(unnamed-54)",20912,1880722,1.1,"Swing Trader"),
(55,"speeda",20527,971739,2.1,"Swing Trader"),
(56,"InsiderrrZ",20527,102163,20.1,"Sharp Selector"),
(57,"1pixel",20471,761303,2.7,"Swing Trader"),
(58,"wegotit2green",20397,452677,4.5,"Swing Trader"),
(59,"dpnd",20185,12204297,0.17,"Volume Whale"),
(60,"(unnamed-60)",19850,761472,2.6,"Swing Trader"),
(61,"syacxxa",19301,495571,3.9,"Swing Trader"),
(62,"soyeon2235",19298,322958,6.0,"Sharp Selector"),
(63,"pandatown",19145,1504733,1.3,"Swing Trader"),
(64,"Varyag",18860,691420,2.7,"Swing Trader"),
(65,"xX25Xx",18841,93610,20.1,"Sharp Selector"),
(66,"OnlyLuckNoBrain",18595,1478734,1.3,"Swing Trader"),
(67,"oVyg7f",18380,5697984,0.32,"Volume Whale,Bot/Algo"),
(68,"TiresOfHondaCivic",18204,476087,3.8,"Multi-Wallet,Swing Trader"),
(69,"cyberkurajber",18110,787541,2.3,"Swing Trader"),
(70,"TheySeemeBuyingTheyHatin",18109,428886,4.2,"Sharp Selector"),
(71,"WeatherHK",17959,448136,4.0,"Domain Expert"),
(72,"securebet",17921,446194,4.0,"Sharp Selector"),
(73,"AB2",17779,591007,3.0,"Swing Trader"),
(74,"PunxsutawneyPhil",17594,529779,3.3,"Domain Expert,Sharp Selector"),
(75,"(unnamed-75)",17216,2152165,0.8,"Volume Whale,Swing Trader"),
(76,"lesse",17181,116754,14.7,"Sharp Selector"),
(77,"fhantombets",17149,167538,10.2,"Sharp Selector"),
(78,"(unnamed-78)",16775,560562,3.0,"Swing Trader"),
(79,"WordleAddict",16265,562376,2.9,"Sharp Selector"),
(80,"bhuumi",16105,3436043,0.47,"Volume Whale,Swing Trader"),
(81,"0bot",16023,574242,2.8,"Bot/Algo"),
(82,"Capillatus",15932,359186,4.4,"Domain Expert"),
(83,"huskyvs",15898,661298,2.4,"Swing Trader"),
(84,"0xhana",15799,321617,4.9,"Sharp Selector"),
(85,"PX5300",15701,2276751,0.69,"Volume Whale,Swing Trader"),
(86,"Miojinho",15613,69002,22.6,"Sharp Selector"),
(87,"justabot0",15439,751523,2.1,"Bot/Algo"),
(88,"MtnMark",15404,52941,29.1,"Sharp Selector,Domain Expert"),
(89,"(unnamed-89)",15099,294971,5.1,"Sharp Selector"),
(90,"sakula1",15019,539752,2.8,"Swing Trader"),
(91,"mjf02",14775,698335,2.1,"Swing Trader"),
(92,"(unnamed-92)",14764,713335,2.1,"Swing Trader"),
(93,"Billy-Ray",14701,1087846,1.4,"Swing Trader"),
(94,"738925",14321,3253278,0.44,"Volume Whale,Swing Trader"),
(95,"GbushiCshuo",14236,3997602,0.36,"Volume Whale,Swing Trader"),
(96,"ocelot-204",13662,83819,16.3,"Sharp Selector"),
(97,"mkuu",13556,62875,21.6,"Sharp Selector"),
(98,"gghff",13554,2031278,0.67,"Volume Whale,Swing Trader"),
(99,"teaseer",13495,289519,4.7,"Sharp Selector"),
(100,"samhain4ik",13289,3254435,0.41,"Volume Whale,Swing Trader"),
]

rows = []
for r in raw:
    rows.append({
        'rank': r[0],
        'username': r[1],
        'pnl': float(r[2]),
        'vol': float(r[3]),
        'eff_pct': float(r[4]),
        'strategies': r[5],
        'strat_list': [s.strip() for s in r[5].split(',')]
    })

strategy_types = ['Sharp Selector', 'Swing Trader', 'Volume Whale', 'Multi-Wallet', 'Bot/Algo', 'Domain Expert']
rank_map = {r['rank']: r for r in rows}

print("=== SECTION A: STRATEGY DISTRIBUTION ===")
print(f"{'Strategy':<20} {'Count':>6} {'% of 100':>10} {'Avg PnL ($)':>14} {'Avg Eff%':>10}")
print("-"*64)
for st in strategy_types:
    traders_with = [r for r in rows if st in r['strat_list']]
    count = len(traders_with)
    avg_pnl = sum(r['pnl'] for r in traders_with) / count if count else 0
    avg_eff = sum(r['eff_pct'] for r in traders_with) / count if count else 0
    print(f"{st:<20} {count:>6} {count:>9}% {avg_pnl:>14,.0f} {avg_eff:>9.2f}%")

print()
print("=== SECTION B: TOP-50 THRESHOLD ===")
rank50 = rows[49]
print(f"Rank #50 trader: {rank50['username']}")
print(f"PnL: ${rank50['pnl']:,.0f}")
print(f"Volume: ${rank50['vol']:,.0f}")
print(f"Efficiency: {rank50['eff_pct']}%")
top50 = rows[:50]
avg_pnl_50 = sum(r['pnl'] for r in top50) / 50
min_pnl_50 = min(r['pnl'] for r in top50)
print(f"Average PnL ranks 1-50: ${avg_pnl_50:,.2f}")
print(f"Minimum PnL to enter top 50: ${min_pnl_50:,.0f}")

print()
print("=== SECTION C: HIGH-EFFICIENCY (>10%) ===")
high_eff = sorted([r for r in rows if r['eff_pct'] > 10.0], key=lambda x: x['eff_pct'], reverse=True)
print(f"{'Rank':<6} {'Username':<32} {'PnL':>10} {'Volume':>12} {'Eff%':>7} {'Strategy'}")
print("-"*95)
for r in high_eff:
    print(f"{r['rank']:<6} {r['username']:<32} ${r['pnl']:>9,.0f} ${r['vol']:>11,.0f} {r['eff_pct']:>6.1f}% {r['strategies']}")
print(f"\nTotal count: {len(high_eff)}")
print(f"Average efficiency: {sum(r['eff_pct'] for r in high_eff)/len(high_eff):.2f}%")

print()
print("=== SECTION D: HIGH-VOLUME (>$2M) ===")
high_vol = sorted([r for r in rows if r['vol'] > 2000000], key=lambda x: x['vol'], reverse=True)
print(f"{'Rank':<6} {'Username':<35} {'PnL':>10} {'Volume':>14} {'Eff%':>7}")
print("-"*76)
for r in high_vol:
    print(f"{r['rank']:<6} {r['username']:<35} ${r['pnl']:>9,.0f} ${r['vol']:>13,.0f} {r['eff_pct']:>6.2f}%")
print(f"\nCount: {len(high_vol)} / 100 = {len(high_vol)}%")

print()
print("=== SECTION E: BOT/ALGO TRADERS ===")
bots = [r for r in rows if 'Bot/Algo' in r['strat_list']]
print(f"{'Rank':<6} {'Username':<38} {'PnL':>10} {'Volume':>12} {'Eff%':>7}")
print("-"*78)
for r in bots:
    print(f"{r['rank']:<6} {r['username']:<38} ${r['pnl']:>9,.0f} ${r['vol']:>11,.0f} {r['eff_pct']:>6.2f}%")

print()
print("=== SECTION F: DOMAIN EXPERT TRADERS ===")
experts = [r for r in rows if 'Domain Expert' in r['strat_list']]
print(f"{'Rank':<6} {'Username':<25} {'PnL':>10} {'Volume':>12} {'Eff%':>7}")
print("-"*65)
for r in experts:
    print(f"{r['rank']:<6} {r['username']:<25} ${r['pnl']:>9,.0f} ${r['vol']:>11,.0f} {r['eff_pct']:>6.2f}%")

print()
print("=== SECTION G: MULTI-WALLET CLUSTERS ===")
clusters = [
    ('gopfan cluster', [1, 4]),
    ('aenews cluster (2 confirmed)', [2, 15]),
    ('aenews cluster (+ chilling affiliate)', [2, 15, 19]),
    ('HondaCivic cluster', [12, 43, 68]),
    ('Protrade cluster (2 visible)', [24, 27]),
    ('maskache cluster (1 visible)', [20]),
]
print(f"{'Cluster':<42} {'Combined PnL':>14} {'Combined Vol':>14} {'Comb Eff%':>10}")
print("-"*84)
for cname, cranks in clusters:
    ct = [rank_map[rk] for rk in cranks]
    cp = sum(r['pnl'] for r in ct)
    cv = sum(r['vol'] for r in ct)
    ce = cp/cv*100
    wallets = ", ".join(f"{r['username']}(#{r['rank']})" for r in ct)
    print(f"{cname:<42} ${cp:>13,.0f} ${cv:>13,.0f} {ce:>9.2f}%")
    print(f"  Wallets: {wallets}")

# All cluster combined stats
print()
print("Full wallet listings:")
for cname, cranks in clusters:
    ct = [rank_map[rk] for rk in cranks]
    cp = sum(r['pnl'] for r in ct)
    cv = sum(r['vol'] for r in ct)
    ce = cp/cv*100
    print(f"  {cname}: PnL=${cp:,.0f}  Vol=${cv:,.0f}  Eff={ce:.2f}%")
    for r in ct:
        print(f"    #{r['rank']} {r['username']}: PnL=${r['pnl']:,.0f}, Vol=${r['vol']:,.0f}, Eff={r['eff_pct']}%")
