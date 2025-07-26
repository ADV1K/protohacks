package netkit

import (
	"reflect"
	"testing"
)

type MyType struct {
	A int
	B string
}

func BenchmarkReflectTypeOf(b *testing.B) {
	obj := MyType{A: 42, B: "hello"}
	for i := 0; i < b.N; i++ {
		_ = reflect.TypeOf(obj)
	}
}

func BenchmarkReflectNew(b *testing.B) {
	typ := reflect.TypeOf(MyType{})
	for i := 0; i < b.N; i++ {
		_ = reflect.New(typ).Interface()
	}
}
