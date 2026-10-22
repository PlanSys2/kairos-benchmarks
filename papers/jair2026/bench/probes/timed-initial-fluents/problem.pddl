(define (problem tif1) (:domain tif) (:objects r1 - robot)
 (:init (ready r1) (= (level r1) 0) (at 5 (= (level r1) 10))) (:goal (and (done r1))))
