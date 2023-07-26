from FreeBack.FreeBack.barbybar import *
from FreeBack.FreeBack.alpha import *
import copy


# 复制因子持有策略
# 如果是持有百分位的话需要先排除掉alpha-keep不选择的再进行排序
def getRank(market_, factor, reverse=False):
    name = 'rank_' + factor
    market = copy.copy(market_)
    if 'alpha-keep' in market.columns:
        market_factor = market_[market_['alpha-keep']]
        # 是否由大到小排列（最小的对应最大的值）
        if reverse:
            # alpha-keep为False的记录自动补nan
            market[name] = Rank(-market_factor[factor])
        else:
            market[name] = Rank(market_factor[factor])
    else:
        if reverse:
            market[name] = Rank(-market_[factor])
        else:
            market[name] = Rank(market_[factor])
    return market
    
def batch_carry(market, factor_name, left, right,intervals=1, comm=7, max_vol=0.1, price='open'):
    # 初始化
    def init1(self):
        self.interval = 0
    
    intervals = intervals
    def strat1(self):
        if self.interval%intervals == 0:
            # 是否排除
            if 'alpha-keep' in market.columns:
                cur_market = self.cur_market[self.cur_market['alpha-keep']]
            else:
                cur_market = self.cur_market
        
            # 区间内的转债
            basket_hold = list(cur_market[(cur_market[factor_name]<=right)&(cur_market[factor_name]>left)].index)

            if len(basket_hold) != 0:
                position = self.cur_net/len(basket_hold)
            else:
                position = 0
            self.log("目标持有 %s"%basket_hold)
        #   动态平衡仓位
            # 对于持仓， 不在新篮子中则卖出， 在篮子中的卖出至目标仓位
            for code in self.cur_hold_vol.index:
                # 略过缺失（）
                inmarket = True
                try:
                    self.cur_market.loc[code]
                except:
                    self.log_error('out of market %s'%code)
                    inmarket = False
                if inmarket:
                    # 卖出
                    if code not in basket_hold:
                        # 不在低溢价率组卖出
                        self.log('调出标的 %s'%code)
                        self.sell(code, price=price)
                    # 调整至目标仓位
                    else:
                        hold_vol = self.cur_hold_vol[code]
                        buy_amount = position - hold_vol * self.cur_market['close'].loc[code]
                        buy_vol = buy_amount/self.cur_market['close'].loc[code]
                        if buy_vol > 0:
                            if not self.convertible_delist(code, intervals+1):
                                self.log('加仓 %s'%code)
                                self.buy(code, buy_vol, price=price)
                        else:
                            self.log('减仓 %s'%code)
                            self.sell(code, -buy_vol, price=price)
                # 如果之后无法交易
                if self.convertible_delist(code, intervals+1):
                    self.log('调出标的 %s'%code)
                    self.sell(code, price=price)
            # 篮子外的 下期可以交易
            for code in basket_hold:
                if code not in self.cur_hold_vol.index:
                    if not self.convertible_delist(code, intervals+1):
                        self.log('买入标的 %s'%code)
                        vol = position/self.cur_market['close'].loc[code]
                        self.buy(code, vol, price=price)
        self.interval += 1

    # 修改类
    World.init = init1
    World.strategy = strat1

    world = World(market, comm=comm, max_vol_perbar=max_vol)
    world.run()
    return world


