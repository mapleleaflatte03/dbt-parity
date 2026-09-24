select id from analytics.prod.customers group by 1 having count(*) > 1
