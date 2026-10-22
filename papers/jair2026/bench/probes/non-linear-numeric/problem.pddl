(define (problem nl1) (:domain nl) (:objects r1 - robot)
 (:init (ready r1) (= (speed r1) 0) (= (total-cost) 0)) (:goal (and (done r1)))
 (:metric minimize (total-cost)))
