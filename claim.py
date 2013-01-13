"""ADA Claim Form Fields

all dates formatted '%m/%d/%Y'

HEADER INFORMATION

1. Type of Transaction
   Statement of Actual Services
   Request for Predetermination

2. Predetermination/Preauthorization Number

PRIMARY PAYER INFORMATION

3. Name & Address

OTHER COVERAGE

4. Other Dental or Medical Coverage? (No, Yes)

5. Subscriber Name
6. Date of Birth
7. Gender
8. Subscriber ID
9. Plan/Group Number
10. Relationship (Self, Spouse, Dependent, Other)
11. Other Carrier Name & Address

PRIMARY SUBSCRIBER

12. Name & Address
13. Date of Birth
14. Gender
15. Subscriber ID
16. Plan/Group Number
17. Employer Name

PATIENT INFORMATION

18. Relationship (Self, Spouse, Dependent, Other)
19. Student Status (Full/Part Time)
20. Name & Address
21. Date of Birth (MM/DD/CCYY)
22. Gender
23. Patient ID/Account # (assigned by dentist)

RECORD OF SERVICES

24. Procedure Date
25. Area of Oral Cavity
26. Tooth System
27. Tooth Number(s)
28. Tooth Surface(s)
29. Procedure
30. Description
31. Fee
32. Other Fee(s)
33. Total Fee

34. Place an X on each missing tooth
35. Remarks

AUTHORIZATIONS

36. Patient/Guardian Signature
37. Assignment of Benefits

ANCILLARY INFORMATION

38. Place of Treatment (Office, Hospital, ECF, Other)
39. Number of enclosures
40. Is Treatment for Orthodontics? (No, Yes)
41. Date Appliance Placed
42. Months of Treatment Remaining
43. Replacement of Prosthesis? (No, Yes)
44. Date Prior Placement
45. Treatment Resulting From (Occupational illness, Auto accident, Other accident)
46. Date of Accident
47. Auto Accident State

BILLING DENTIST OR ENTITY

48. Name & Address
49. NPI
50. License Number
51. SSN or TIN
52. Phone Number
52A. Additional Provider ID

TREATING DENTIST

53. Signature
54.  NPI
55. License Number
56. Address
56A. Treating Provider Specialty
57. Phone Number
58. Additional Provider ID

Whew!
"""


import forms
import hello
import model

import web


class update_claim:
    def POST(self, claimid):
        claimid = int(claimid)
        journal = model.get_journal_entry(claimid)
        claim = model.get_claim(claimid)
        txs = model.get_tx_for_claim(claimid)
        pt = model.get_pt(journal.patientid)

        # validate form input
        inp = web.input()
        form = forms.claim()
        if not form.validates(inp):
            plan = model.get_plan(claim.planid)
            return hello.render.claim(pt, claim, form, plan, txs)

        # update the claim
        model.db.update('claim', where='journalid=%d' % journal.id,
                        notes=form.notes.get_value())

        # update the journal
        model.db.update('journal', where='id=%d' % journal.id,
                        summary=form.summary.get_value())

        # now go through and update the treatment
        deltains = 0.0
        deltapt = 0.0
        for tx in txs:
            fee = inp['fee%d' % tx.id]
            if fee:
                fee = float(fee)
            else:
                fee = 0.0
            allowed = inp['allowed%d' % tx.id]
            if allowed:
                allowed = float(allowed)
            else:
                allowed = None
            inspaid = inp['inspaid%d' % tx.id]
            if inspaid:
                inspaid = float(inspaid)
            else:
                inspaid = None
            ptpaid = inp['ptpaid%d' % tx.id]
            if ptpaid:
                ptpaid = float(ptpaid)
            else:
                ptpaid = None

            deltains += (inspaid or 0.0) - float(tx.inspaid or 0.0)
            deltapt += (ptpaid or 0.0) - float(tx.ptpaid or 0.0)

            model.db.update('tx', where='id=%d' % tx.id,
                            fee=fee,
                            allowed=allowed,
                            inspaid=inspaid,
                            ptpaid=ptpaid)

        if deltains >= 0.01:
            model.new_payment_for_pt(pt, 'insurance payment', -deltains)
        if deltapt >= 0.01:
            model.new_payment_for_pt(pt, 'patient payment', -deltapt)

        raise web.seeother('/journal/%d' % journal.id)
