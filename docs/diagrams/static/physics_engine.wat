(module
  ;; Import JavaScript memory
  (import "js" "mem" (memory 1))
  
  ;; Import math functions
  (import "Math" "sin" (func $sin (param f64) (result f64)))
  (import "Math" "cos" (func $cos (param f64) (result f64)))
  
  ;; Vector operations in linear memory
  (func $vectorAdd (param $x1 f64) (param $y1 f64) (param $x2 f64) (param $y2 f64) (result f64 f64)
    (f64.add (local.get $x1) (local.get $x2))
    (f64.add (local.get $y1) (local.get $y2))
  )
  
  ;; Spring physics calculation
  (func $calculateSpringForce (param $k f64) (param $x f64) (result f64)
    (f64.mul (local.get $k) (local.get $x))
  )
  
  ;; Particle movement with damping
  (func $updateParticle 
    (param $x f64) (param $y f64) 
    (param $vx f64) (param $vy f64)
    (param $dt f64) (param $damping f64)
    (result f64 f64 f64 f64)
    
    ;; Update position
    (f64.add (local.get $x) 
      (f64.mul (local.get $vx) (local.get $dt)))
    (f64.add (local.get $y)
      (f64.mul (local.get $vy) (local.get $dt)))
    
    ;; Apply damping to velocity
    (f64.mul (local.get $vx) (local.get $damping))
    (f64.mul (local.get $vy) (local.get $damping))
  )
  
  ;; Export functions
  (export "vectorAdd" (func $vectorAdd))
  (export "calculateSpringForce" (func $calculateSpringForce))
  (export "updateParticle" (func $updateParticle))
)
