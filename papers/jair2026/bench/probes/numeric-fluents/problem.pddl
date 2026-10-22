(define (problem nf1) (:domain nf) (:objects r1 - robot)
 (:init (ready r1) (= (load r1) 0) (= (total-cost) 0)) (:goal (and (done r1)))
 (:metric minimize (total-cost)))
