from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
import scipy.optimize

class Bond:

    def _init_(self, issue, maturity, cpn, period, amortization):

        self._issue = issue #issue date
        self._mat = maturity #date of bond's last payment
        self._cpn = cpn #yearly cupon
        self._period = period #number of payments per year
        self._amort = amortization
        self._calc_cshf() #initiate cashflow calculation

    def _str_(self):
        return f'{self._dates} , {self._cshf}'

    def _calc_cshf(self): #we calculate the bonds payment days and cash payments
        date = self._issue + relativedelta(months= (12 / self._period)) #we search for the first payment
        self._dates = []

        while date < self._mat: #we correct for payments in the weekend
            if date.isoweekday() in set((6, 7)):
                day = date + timedelta(days=8 - date.isoweekday())
            else:
                day = date
            self._dates.append(day)
            date += relativedelta(months= (12/self._period))

        self._dates.append(self._mat)
        self._cshf = []
        cupon = self._cpn / self._period

        for i in range(len(self._dates) - 1):
            self._cshf.append(cupon)
        self._cshf.append(self._amort + cupon)

    def get_cashflow_at_date(self, calc_date): #we calculate the cashflow at a specific date (ignorin previous payments)
        for i in range(len(self._dates)):
            if self._dates[i] > calc_date:
                break
        return [(self._dates[x], self._cshf[x]) for x in range(i, len(self._dates))]

    def _xnpv(self,rate,cashflow):
        if rate <= -1.0:
            return float('inf')
        d0 = cashflow[0][0]
        return sum([vi / (1.0 + rate) ** ((di - d0).days / 365.0) for di, vi in cashflow])

    def xirr(self, date, px):
        cashflow = self.get_cashflow_at_date(date)
        cashflow.insert(0,(date,-px))

        try:
            return scipy.optimize.newton(lambda r: self._xnpv(r, cashflow), 0.0)
        except RuntimeError:  # Failed to converge?
            return scipy.optimize.brentq(lambda r: self._xnpv(r, cashflow), -1.0, 1e10)

    def tir_a_tna(self,date,px):
        dias = (self._mat - date).days
        if dias < 180:
            return ((1 + self.xirr(date,px))**(dias/365)-1)*365/dias
        else:
            return ((1 + self.xirr(date, px)) ** (182.5 / 365) - 1) * 360 / 180

    def tna_a_tir(self, rate):
        return (rate * 180 / 360 + 1) ** (365 / 182.5) - 1

    def tna_a_px(self, rate, date):

        cashflow = self.get_cashflow_at_date(date)
        tir = self.tna_a_tir(rate)
        price = [cashflow[i][1]/((1+tir)**((cashflow[i][0]-date).days/365)) for i in range(len(cashflow))]
        return price

    def duration(self, date, rate):
        price = self.tna_a_px(rate, date)
        cashflow = self.get_cashflow_at_date(date)
        dur = sum(price[i]*(cashflow[i][0]-date).days/365/sum(price) for i in range(len(price)))
        return dur

    def md_duration(self, date, rate):
        return self.duration(date, rate) / (1 + self.tna_a_tir(rate) / self._period)



if __name__ == "main":

    day = date.date(2022, 6, 6)
    bond1 = Bond(date(2020, 10, 29), date(2026, 4, 29), 0.1, 2, 100)
    print(bond1.tna_a_px(0.05,day))
